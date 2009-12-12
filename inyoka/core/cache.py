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
from os.path import join
from werkzeug.contrib.cache import NullCache, SimpleCache, FileSystemCache, \
     MemcachedCache
from inyoka.core.config import config


cache = (type('UnconfiguredCache', (NullCache,), {}))()


#: the cache system factories.
systems = {
    'null':         lambda: NullCache(),
    'simple':       lambda: SimpleCache(config['caching.timeout']),
    'memcached':    lambda: MemcachedCache(
        [x.strip() for x in config['caching.memcached_servers']],
        config['caching.timeout']),
    'filesystem':   lambda: FileSystemCache(
        join(os.environ['package_folder'],
             config['caching.filesystem_cache_path']),
        threshold=500,
        default_timeout=config['caching.timeout'])
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
