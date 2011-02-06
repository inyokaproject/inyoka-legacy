# -*- coding: utf-8 -*-
"""
    inyoka.core.cache
    ~~~~~~~~~~~~~~~~~

    Caching interface for Inyoka.  It supports various caching systems,
    amongst others:

     * Filesystem cache
     * Memcache

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import time
import random
from os.path import join
from datetime import datetime
from functools import wraps
from werkzeug.contrib.cache import NullCache, SimpleCache, FileSystemCache, \
     MemcachedCache, BaseCache, GAEMemcachedCache
from inyoka.context import ctx
from inyoka.core.database import db
from inyoka.core.models import Cache
from inyoka.core.config import TextConfigField, IntegerConfigField

__all__ = ('cache',)

cache = (type('UnconfiguredCache', (NullCache,), {}))()

#: Set the caching system.  Choose one of ’null’, ’simple’, ’memcached’ or ’filesystem’.
caching_system = TextConfigField('caching.system', default=u'null')

#: Set the path for the filesystem caches
caching_filesystem_cache_path = TextConfigField('caching.filesystem_cache_path',
                                          default=u'/tmp/_inyoka_cache')

#: Set the timeout for the caching system
caching_timeout = IntegerConfigField('caching.timeout', default=300, min_value=10)

#: Set the memcached servers.  Comma seperated list of memcached servers
caching_memcached_servers = TextConfigField('caching.memcached_servers', default=u'')



class DatabaseCache(BaseCache):
    """Database cache backend using Inyokas database framework.

    :param default_timeout:  The timeout a key is valid to use.
    :param max_entries:      The maximum number of entries in the cache.
    :param maxcull:          The maximum number of entries to cull per call if
                             cache is full.
    """

    def __init__(self, default_timeout=300, max_entries=300, maxcull=10):
        BaseCache.__init__(self, default_timeout)
        self.max_entries = max_entries
        self.maxcull = maxcull

    def get(self, key):
        """Return the cached value or `None`.

        :param key: The key to retrieve.
        """
        item = db.session.query(Cache).filter_by(key=key).first()
        if item is not None:
            # remove if item exired
            if item.expires < datetime.now().replace(microsecond=0):
                self.delete(key)
                return None
            return item.value

    def delete(self, key):
        """Delete all cached values for `key`"""
        db.session.query(Cache).filter_by(key=key).delete()

    def get_many(self, keys):
        """Return a list of values cached with one key of `keys`.

        :param keys: A list of keys to retrieve.
        """
        return db.session.query(Cache.value).fitler(Cache.key.in_(keys)).all()

    def get_dict(self, *keys):
        """Return a key/value dictionary for all `keys`"""
        result = db.session.query(Cache).filter(Cache.key.in_(keys)).all()
        return {x.key: x.value for x in result}

    def set(self, key, value, timeout=None, overwrite=True):
        """Set a cached value.

        :param key: The key to identify the cached value.
        :param value: The value to cache.
        :param timeout: The timeout in seconds till the key decays.
        :param overwrite: Overwrite existing values or not.
        """
        if timeout is None:
            timeout = self.default_timeout

        if len(self) >= self.max_entries:
            self._cull()

        expires = datetime.fromtimestamp(
            time.time() + timeout
        ).replace(microsecond=0)

        # Update database if key already present
        if key in self:
            if overwrite:
                db.session.query(Cache).filter_by(key=key).update({
                    'value': value,
                    'expires': expires,
                })
        else:
            # insert new key if key not present
            Cache(key=key, value=value, expires=expires)
            db.session.commit()

    def add(self, key, value, timeout=None):
        """Same as :method:`set` but does not overwrite values per default."""
        self.set(key, value, timeout, overwrite=False)

    def set_many(self, mapping, timeout=None):
        """Set many values for caching.

        :param mapping: A dictionary containing the key/value pairs.
        """
        for key, value in mapping.iteritems():
            self.set(key, value, timeout)

    def delete_many(self, *keys):
        """Delete many cached values"""
        db.session.query(Cache).filter(Cache.key.in_(keys)).delete()

    def _cull(self):
        """Remove not used or expired items in cache."""
        # remove items that have timed out
        now = datetime.now().replace(microsecond=0)
        db.session.query(Cache).filter(Cache.expires < now).delete()
        # remove any items over the maximum allowed number in the cache
        if len(self) >= self.max_entries:
            # upper limit for key query
            ul = self.maxcull * 2
            # get list of keys
            keys = db.session.query(Cache.key).filter_by(limit=ul).all()
            # get some keys at random
            delkeys = list(random.choice(keys) for i in xrange(self.maxcull))
            # delete keys
            db.session.query(Cache).filter(Cache.key.in_(delkeys)).delete()

    def __contains__(self, key):
        value = self.get(key)
        if value is not None:
            return True
        return False

    def __len__(self):
        return db.session.query(Cache).count()



def cached(timeout=None, key_prefix='view/%s', unless=None):
    """Decorator.  Use this to cache a function.

    By default the cache key is `view/request.path`.  You are able to
    use this decorator with any function by changing the `key_prefix`.
    If the token `%s` is located within the `key_prefix` then it will
    be replaced with `request.path`.

    Example::

        # An example view function
        @cached(timeout=50)
        def big_foo():
            return big_bar_calc()

        # An example misc function to cache.
        @cached(key_prefix='MyCachedList')
        def get_list():
            return [random.randrange(0, 1) for i in range(50000)]

    .. note::

        You MUST have a request context to actually called any functions
        that are cached if you are using the request.path formatter.

    :param timeout: Default None. If set to an integer, will cache for that
                    amount of time. Unit of time is in seconds.
    :param key_prefix: Default 'view/%(request.path)s'. Beginning key to .
                       use for the cache key.
    :param unless: Default None. Cache will *always* execute the caching
                   facilities unless this callable is true.
                   This will bypass the caching entirely.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            #: Bypass the cache entirely.
            if callable(unless) and unless() is True:
                return f(*args, **kwargs)

            if '%s' in key_prefix:
                cache_key = key_prefix % ctx.current_request.path
            else:
                cache_key = key_prefix

            rv = cache.get(cache_key)
            if rv is None:
                rv = f(*args, **kwargs)
                cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator


#: A list holding all used cache-keys used by the memoized decorator.
_memoized = []


def memoize(timeout=None):
    """Decorator.  Use this to cache the result of a function,
    taking it's arguments into account in the cache key.

    For more information, see `Memoization <http://en.wikipedia.org/wiki/Memoization>`_.

    Example::

        @memoize(timeout=50)
        def big_foo(a, b):
            return a + b + random.randrange(0, 1000)

    :param timeout: Default None. If set to an integer, will cache for that
                    amount of time. Unit of time is in seconds.
    """
    def memoize(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = ('memoize', f.__name__, id(f), args, str(kwargs))

            rv = cache.get(cache_key)
            if rv is None:
                rv = f(*args, **kwargs)
                cache.set(cache_key, rv, timeout=timeout)
                if cache_key not in _memoized:
                    _memoized.append(cache_key)
            return rv
        return decorated_function
    return memoize


def clear_memoized(*keys):
    """Deletes all of the cached functions that used Memoize for caching.

    Example::

        @cache.memoize(50)
        def random_func():
        return random.randrange(1, 50)

    :param *keys: A list of function names to clear from cache.
    """
    global _memoized
    def deletes(item):
        if item[0] == 'memoize' and item[1] in keys:
            cache.delete(item)
            return True
        return False

    _memoized[:] = [x for x in _memoized if not deletes(x)]


#: the cache system factories.
CACHE_SYSTEMS = {
    'null': lambda: NullCache(),
    'simple': lambda: SimpleCache(ctx.cfg['caching.timeout']),
    'memcached': lambda: MemcachedCache(
        [x.strip() for x in ctx.cfg['caching.memcached_servers'].split(',')],
        ctx.cfg['caching.timeout']),
    'filesystem': lambda: FileSystemCache(
        join(ctx.cfg['caching.filesystem_cache_path']),
        threshold=500,
        default_timeout=ctx.cfg['caching.timeout']),
    'database': lambda: DatabaseCache(ctx.cfg['caching.timeout']),
    'gaememcached': lambda: GAEMemcachedCache(ctx.cfg['caching.timeout'])
}


def set_cache():
    """Set and return the cache for the application.  This is called during
    the application setup.  No need to call that afterwards.
    """
    global cache
    cache = CACHE_SYSTEMS[ctx.cfg['caching.system']]()
    return cache

# enable the caching system
set_cache()
