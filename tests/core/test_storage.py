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
from inyoka.core.storage import CachedStorage
from inyoka.core.models import Storage


ITEMS1 = [u'foobar', 1, 1.5, [u'asd', u'ümlauts'], {u'foo': u'bar'}]
ITEMS2 = [u'barfoo', 2, 5.1, [u'ümlauts', u'asd'], {u'bar': u'foo'}]
DICT_1 = dict((u'key_%d' % i, v) for i, v in enumerate(ITEMS1))
DICT_2 = dict((u'key_%d' % i, v) for i, v in enumerate(ITEMS2))


class TestStorage(DatabaseTestCase):

    def setUp(self):
        self._configured_cache = ctx.cfg['caching.system']
        ctx.cfg['caching.system'] = 'simple'
        self.cache = set_cache()
        self.storage = CachedStorage(self.cache)

    def tearDown(self):
        ctx.cfg['caching.system'] = self._configured_cache
        Storage.query.delete()
        self.cache = set_cache()
        self.storage = CachedStorage(self.cache)

    def test_storage_get(self):
        # setup the storage
        for key, value in DICT_1.iteritems():
            self.assertEqual(self.cache.get(u'storage/%s' % key), None)
            self.storage.set(key, value)

        for key, value in DICT_1.iteritems():
            cache_key = u'storage/%s' % key
            # check whether it was also written to the cache
            print self.cache, cache_key, value, self.cache._cache
            self.assertEqual(self.cache.get(cache_key), value)
            # check whether retrieving storage data of the cache works
            self.assertEqual(self.storage.get(key), value)
            # check whether retrieving storage data without cache works
            self.cache.delete(cache_key)
            self.assertEqual(self.storage.get(key), value)
            # check whether storage.get wrote the data to the cache
            self.assertEqual(self.cache.get(cache_key), value)

        # and cleanup the storage
        self.cache.delete_many(*DICT_1.keys())

    def test_storage_get_many(self):
        # check whether storage.set works well for already existing keys
        for key, value in DICT_2.iteritems():
            self.storage.set(key, value)

        for key, value in self.storage.get_many(DICT_2.keys()).iteritems():
            self.assertEqual(value, DICT_2[key])
            # check whether storage.get_many wrote the data to the cache
            self.assertEqual(self.cache.get(u'storage/%s' % key), value)

        # check whether get_many works well if the data isn't in the cache anymore
        self.cache.delete_many(*DICT_2.keys())

        for key, value in self.storage.get_many(DICT_2.keys()).iteritems():
            self.assertEqual(value, DICT_2[key])
            # check whether storage.get_many wrote the data to the cache
            self.assertEqual(self.cache.get(u'storage/%s' % key), value)
