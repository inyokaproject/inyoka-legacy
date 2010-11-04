# -*- coding: utf-8 -*-
"""
    tests.core.test_subscriptions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for the subscription system.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import db, ctx
from inyoka.core.test import *
from inyoka.core.cache import cache, set_cache
from inyoka.core.storage import storage


ITEMS1 = [u'foobar', 1, 1.5, [u'asd', u'ümlauts'], {u'foo': u'bar'}]
ITEMS2 = [u'barfoo', 2, 5.1, [u'ümlauts', u'asd'], {u'bar': u'foo'}]
DICT_1 = dict((u'key_%d' % i, v) for i, v in enumerate(ITEMS1))
DICT_2 = dict((u'key_%d' % i, v) for i, v in enumerate(ITEMS2))

_configured_cache = None


def setup():
    global _configured_cache
    _configured_cache = ctx.cfg['caching.system']
    ctx.cfg['caching.system'] = 'simple'
    set_cache()


def shutdown():
    ctx.cfg['caching.system'] = _configured_cache


@refresh_database
@with_setup(setup, shutdown)
def test():
    def test_get(d):
        for k, v in d.iteritems():
            cache_key = u'storage/%s' % k
            # check whether it was also written to the cache
            eq_(cache.get(cache_key), v)
            # check whether retrieving storage data of the cache works
            eq_(storage.get(k), v)
            # check whether retrieving storage data without cache works
            cache.delete(cache_key)
            eq_(storage.get(k), v)
            # check whether storage.get wrote the data to the cache
            eq_(cache.get(cache_key), v)

    def test_get_many(d):
        for k, v in storage.get_many(d.keys()).iteritems():
            eq_(v, d[k])
            # check whether storage.get_many wrote the data to the cache
            eq_(cache.get(u'storage/%s' % k), v)

    # check whether storage.set works well for new keys
    for k, v in DICT_1.iteritems():
        eq_(cache.get(u'storage/%s' % k), None)
        storage.set(k, v)

    test_get(DICT_1)
    cache.delete_many(*DICT_1.keys())

    # check whether storage.set works well for already existing keys
    for k, v in DICT_2.iteritems():
        storage.set(k, v)

    test_get(DICT_2)

    # check whether get_many works well if the data is still in the cache
    test_get_many(DICT_2)

    # check whether get_many works well if the data isn't in the cache anymore
    cache.delete_many(*DICT_2.keys())
    test_get_many(DICT_2)
