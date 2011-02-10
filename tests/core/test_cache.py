# -*- coding: utf-8 -*-
"""
    test_database
    ~~~~~~~~~~~~~

    Unittests for our database framework and utilities.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import time
import random
from inyoka.core.test import *
from inyoka.core.cache import cache, memoize, cached, set_cache, clear_memoized


class CacheTestCase(ViewTestCase):

    def setUp(self):
        self._configured_cache = ctx.cfg['caching.system']
        ctx.cfg['caching.system'] = 'simple'
        self.cache = set_cache()

    def tearDown(self):
        ctx.cfg['caching.system'] = self._configured_cache
        self.cache = set_cache()

    # test basic API but do not test details as those are tested in
    # upstream unittest suites.

    def test_cache_set(self):
        self.cache.set('hi', 'hello')
        self.assertEqual(self.cache.get('hi'), 'hello')

    def test_cache_add(self):
        self.cache.add('hi', 'hello')
        self.assertEqual(self.cache.get('hi'), 'hello')
        self.cache.add('hi', 'foobar')
        self.assertEqual(self.cache.get('hi'), 'hello')

    def test_cache_delete(self):
        self.cache.set('hi', 'hello')
        self.cache.delete('hi')
        self.assertTrue(self.cache.get('hi') is None)

    def test_cached_function(self):
        with self.get_new_request():
            @cached(2, key_prefix='MyBits')
            def get_random_bits():
                return [random.randrange(0, 2) for i in range(50)]

            my_list = get_random_bits()
            his_list = get_random_bits()

            self.assertEqual(my_list, his_list)

            time.sleep(4)
            his_list = get_random_bits()

            self.assertNotEqual(my_list, his_list)

    def test_cached_function_unless(self):
        with self.get_new_request():
            @cached(5, unless=lambda: True)
            def non_cached_view():
                return str(time.time())

            @cached(5, unless=lambda: False)
            def cached_view():
                return str(time.time())

            the_time = non_cached_view()
            time.sleep(1)
            the_new_time = non_cached_view()
            self.assertNotEqual(the_time, the_new_time)

            the_time = cached_view()
            time.sleep(1)
            the_new_time = cached_view()
            self.assertEqual(the_time, the_new_time)

    def test_cached_out_of_request_context(self):
        @cached(5)
        def cached_view():
            return u'Foo'

        with self.assertRaises(RuntimeError):
            cached_view()

    def test_memoize(self):
        with self.get_new_request():
            @memoize(5)
            def big_foo(a, b):
                return a+b+random.randrange(0, 100000)

            result = big_foo(5, 2)
            time.sleep(1)

            self.assertEqual(big_foo(5, 2), result)

            result2 = big_foo(5, 3)
            self.assertNotEqual(result2, result)

            time.sleep(4)

            self.assertNotEqual(big_foo(5, 2), result)
            self.assertEqual(big_foo(5, 3), result2)

            time.sleep(1)

            self.assertNotEqual(big_foo(5, 3), result2)

    def test_clear_memoize(self):
        with self.get_new_request():
            @memoize(5)
            def big_foo(a, b):
                return a+b+random.randrange(0, 100000)

            result = big_foo(5, 2)
            time.sleep(1)
            self.assertEqual(big_foo(5, 2), result)
            clear_memoized('big_foo')
            self.assertNotEqual(big_foo(5, 2), result)


class TestDatabaseCache(ViewTestCase):

    def setUp(self):
        self._configured_cache = ctx.cfg['caching.system']
        ctx.cfg['caching.system'] = 'database'
        self.cache = set_cache()

    def tearDown(self):
        ctx.cfg['caching.system'] = self._configured_cache
        self.cache = set_cache()

    # test basic API but do not test details as those are tested in
    # upstream unittest suites.

    def test_set(self):
        self.cache.set(u'hi', u'hello')
        self.assertEqual(self.cache.get(u'hi'), u'hello')

    def test_add(self):
        self.cache.add(u'hi', u'hello')
        self.assertEqual(self.cache.get(u'hi'), u'hello')
        self.cache.add(u'hi', u'foobar')
        self.assertEqual(self.cache.get(u'hi'), u'hello')

    def test_delete(self):
        self.cache.set(u'hi', u'hello')
        self.cache.delete(u'hi')
        self.assertTrue(self.cache.get(u'hi') is None)

    def test_get(self):
        self.cache.set(u'hi', u'hello', timeout=2)
        self.assertEqual(self.cache.get(u'hi'), u'hello')
        time.sleep(3)
        self.assertNotEqual(self.cache.get(u'hi'), u'hello')

    def test_get_many(self):
        self.cache.set(u'hi1', u'hello1')
        self.cache.set(u'h12', u'hello2')
        self.cache.set(u'hi3', u'hello3')
        self.assertEqual(self.cache.get_many((u'hi1', u'hi3')),
                         [u'hello1', u'hello3'])

    def test_get_dict(self):
        self.cache.set(u'hi1', u'hello1')
        self.cache.set(u'h12', u'hello2')
        self.cache.set(u'hi3', u'hello3')
        self.assertEqual(self.cache.get_dict(u'hi1', u'hi3'),
                         {u'hi1': u'hello1', u'hi3': u'hello3'})

    def test_set_many(self):
        self.cache.set_many({u'hi1': u'hello1', u'hi5': u'hello5'}, timeout=2)
        self.assertEqual(self.cache.get(u'hi1'), u'hello1')
        self.assertEqual(self.cache.get(u'hi5'), u'hello5')
        time.sleep(3)
        self.assertNotEqual(self.cache.get(u'hi1'), u'hello1')
        self.assertNotEqual(self.cache.get(u'hi5'), u'hello5')

    def test_delete_many(self):
        self.cache.set_many({u'hi1': u'hello1', u'hi5': u'hello5'}, timeout=2)
        self.assertEqual(self.cache.get(u'hi1'), u'hello1')
        self.cache.delete_many(u'hi1', u'hi5')
        self.assertNotEqual(self.cache.get(u'hi1'), u'hello1')
        self.assertNotEqual(self.cache.get(u'hi5'), u'hello5')
