# -*- coding: utf-8 -*-
"""
    test_context
    ~~~~~~~~~~~~

    Tests for :mod:`inyoka.context` module.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.context import LocalProperty, local, _lookup_object, local_manager
from inyoka.core.api import ctx


_test = local('test')


class DummyClass(object):
    request = LocalProperty('request')


class TestContext(ViewTestCase):

    def test_lookup_object(self):
        # we're outside of a request context
        self.assertRaises(RuntimeError, _lookup_object, 'request')
        # get into request context
        with self.get_new_request():
            self.assertTrue(_lookup_object('request') is not None)

    def test_local_property(self):
        cls = DummyClass()
        # return None in case of RuntimeError
        self.assertTrue(cls.request is None)
        # returns the request object once we got an request context
        with self.get_new_request():
            self.assertTrue(cls.request is not None)
