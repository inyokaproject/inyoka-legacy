# -*- coding: utf-8 -*-
"""
    inyoka.core.cache
    ~~~~~~~~~~~~~~~~~

    Caching interface for Inyoka.  It supports various caching systems,
    amongst others:

     * Filesystem cache
     * Memcache

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import time
import random
from operator import attrgetter
from datetime import datetime
from os.path import join
from werkzeug.contrib.cache import NullCache, SimpleCache, FileSystemCache, \
     MemcachedCache, BaseCache
from inyoka.core.config import config
from inyoka.core.database import db

__all__ = ('cache',)

cache = (type('UnconfiguredCache', (NullCache,), {}))()


class Cache(db.Model):
    __tablename__ = 'core_cache'

    key = db.Column(db.String(60), primary_key=True, nullable=False)
    value = db.Column(db.PickleType, nullable=False)
    expires = db.Column(db.DateTime, nullable=False)


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
        item = db.session.query(Cache).filter_by(key=key).first()
        if item is not None:
            # remove if item exired
            if item.expires < datetime.now().replace(microsecond=0):
                self.delete(key)
                return None
            return item.value

    def delete(self, key):
        db.session.query(Cache).filter_by(key=key).delete()

    def get_many(self, keys):
        return db.session.query(Cache.value).fitler(Cache.key.in_(keys)).all()

    def get_dict(self, *keys):
        result = db.session.query(Cache).filter(Cache.key.in_(keys)).all()
        return dict((x.key, x.value) for x in result)

    def set(self, key, value, timeout=None, override=True):
        if timeout is None:
            timeout = self.default_timeout

        if len(self) >= self.max_entries:
            self._cull()

        expires = datetime.fromtimestamp(
            time.time() + timeout
        ).replace(microsecond=0)

        # Update database if key already present
        if key in self:
            if override:
                db.session.query(Cache).filter_by(key=key).update({
                    'value': value,
                    'expires': expires,
                })
        else:
            # insert new key if key not present
            obj = Cache(key=key, value=value, expires=expires)
            db.session.add(obj)
            db.session.commit()

    def add(self, key, value, timeout=None):
        self.set(key, value, timeout, override=False)

    def set_many(self, mapping, timeout=None):
        for key, value in mapping.iteritems():
            self.set(key, value, timeout)

    def delete_many(self, *keys):
        db.session.query(Cache).filter(Cache.key.in_(keys)).delete()

    def _cull(self):
        """Remove not used or expired items in cache."""
        # remove items that have timed out
        now = datetime.now().replace(microsecond=0)
        db.session.query(Cache).filter(Cache.expires < now).delete()
        # remove any items over the maximum allowed number in the cache
        if len(self) >= self.max_entries:
            # upper limit for key query
            ul = maxcull * 2
            # get list of keys
            keys = db.session.query(Cache.key).filter_by(limit=ul).all()
            # get some keys at random
            delkeys = list(random.choice(keys) for i in xrange(maxcull))
            # delete keys
            db.session.query(Cache).filter(Cache.key.in_(delkeys)).delete()

    def __contains__(self, key):
        value = self.get(key)
        if value is not None:
            return True
        return False

    def __len__(self):
        return db.session.query(Cache).count()


#: the cache system factories.
systems = {
    'null':         lambda: NullCache(),
    'simple':       lambda: SimpleCache(config['caching.timeout']),
    'memcached':    lambda: MemcachedCache(
        [x.strip() for x in config['caching.memcached_servers'].split(',')],
        config['caching.timeout']),
    'filesystem':   lambda: FileSystemCache(
        join(config['caching.filesystem_cache_path']),
        threshold=500,
        default_timeout=config['caching.timeout']),
    'database':     lambda: DatabaseCache(config['caching.timeout'])
}


def set_cache():
    """Set and return the cache for the application.  This is called during
    the application setup.  No need to call that afterwards.
    """
    global cache
    cache = systems[config['caching.system']]()
    return cache

# enable the caching system
set_cache()