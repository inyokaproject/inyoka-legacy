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
import pickle
from datetime import datetime
from os.path import join
from werkzeug.contrib.cache import NullCache, SimpleCache, FileSystemCache, \
     MemcachedCache, BaseCache
from inyoka.core.config import config
from inyoka.core.database import db

__all__ = ('cache',)

cache = (type('UnconfiguredCache', (NullCache,), {}))()

_meta = db.metadata
_meta.bind = db.get_engine()
_cache_table = db.Table('core_cache', _meta,
    db.Column('key', db.String(60), primary_key=True, nullable=False),
    db.Column('value', db.Binary, nullable=False),
    db.Column('expires', db.DateTime, nullable=False))


class DatabaseCache(BaseCache):
    """Database cache backend

    :param default_timeout:  The timeout a key is valid to use.
    :param max_entries:      The maximum number of entries in the cache.
    :param maxcull:          The maximum number of entries to cull per call if
                             cache is full.
    """

    def __init__(self, default_timeout=300, max_entries=300, maxcull=10):
        BaseCache.__init__(self, default_timeout)

        # create cache table if not exists
        if not _cache_table.exists():
            _cache_table.create()

        self.max_entries = max_entries
        self.maxcull = maxcull

    def get(self, key):
        engine = db.get_engine()
        row = engine.execute(db.select(
            [_cache_table.c.value, _cache_table.c.expires],
            _cache_table.c.key==key
        )).fetchone()
        if row is not None:
            # remove if item exired
            if row.expires < datetime.now().replace(microsecond=0):
                self.delete(key)
                return None
            return pickle.loads(row.value)

    def __contains__(self, key):
        value = self.get(key)
        if value is not None:
            return True
        return False

    def __len__(self):
        engine = db.get_engine()
        return engine.execute(db.select(
            [_cache_table.count()]
        )).fetchone()[0]

    def set(self, key, value, timeout=None):
        engine = db.get_engine()
        if timeout is None:
            timeout = self.default_timeout
        value, cache = pickle.dumps(value), _cache_table

        if len(self) >= self.max_entries:
            self._cull()

        expires = datetime.fromtimestamp(
            time.time() + timeout
        ).replace(microsecond=0)

        # Update database if key already present
        if key in self:
            engine.execute(db.update(cache,
                cache.c.key==key,
                dict(value=value, expires=expires)
            ))
        else:
            # insert new key if key not present
            engine.execute(db.insert(cache,
                dict(key=key, value=value, expires=expires)
            ))

    def delete(self, key):
        db.get_engine().execute(db.delete(_cache_table,
            _cache_table.c.key==key
        ))

    def _cull(self):
        """Remove not used or expired items in cache."""
        engine = db.get_engine()
        cache, maxcull = _cache_table, self.maxcull
        # remove items that have timed out
        now = datetime.now().replace(microsecond=0)
        engine.execute(db.delete(cache, cache.c.expires < now))
        # remove any items over the maximum allowed number in the cache
        if len(self) >= self.max_entries:
            # upper limit for key query
            ul = maxcull * 2
            # get list of keys
            keys = [i[0] for i in engine.execute(db.select(
                [cache.c.key], limit=ul)).fetchall()
            ]
            # get some keys at random
            delkeys = list(random.choice(keys) for i in xrange(maxcull))
            # delete keys
            fkeys = tuple({'key': k} for k in delkeys)
            engine.execute(db.delete(cache,
                cache.c.key.in_(db.bindparam('key')
            )), *fkeys)


#: the cache system factories.
systems = {
    'null':         lambda: NullCache(),
    'simple':       lambda: SimpleCache(config['caching.timeout']),
    'memcached':    lambda: MemcachedCache(
        [x.strip() for x in config['caching.memcached_servers'].split(',')],
        config['caching.timeout']),
    'filesystem':   lambda: FileSystemCache(
        join(os.environ['package_folder'],
             config['caching.filesystem_cache_path']),
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
