# -*- coding: utf-8 -*-
"""
    test_decorators
    ~~~~~~~~~~~~~~~

    Unittests for our decorator utilities.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.utils.decorators import abstract, make_decorator, update_wrapper


def test_abstract_raises():
    class SomeInterface(object):
        @abstract
        def process(self):
            pass

    class BadImplementation(SomeInterface):
        pass

    class FineImplementation(SomeInterface):
        def process(self):
            return True

    obj = BadImplementation()
    assert_raises(NotImplementedError, obj.process)
    obj2 = FineImplementation()
    assert_true(obj2.process())


def test_make_decorator():
    decorator = make_decorator('alias')

    @decorator
    def some_func():
        return 5

    eq_(some_func.alias, 'some_func')
    eq_(some_func(), 5)

    @decorator()
    def some_func():
        return 5

    eq_(some_func.alias, 'some_func')
    eq_(some_func(), 5)

    @decorator('other_alias')
    def some_func():
        return 5

    eq_(some_func.alias, 'other_alias')
    eq_(some_func(), 5)


def test_update_wrapper():
    def proxy(func):
        return func

    def func(foo='bar'):
        """doc"""
        print foo

    new = update_wrapper(proxy, func)
    assert_equals(new.signature, (['foo'], None, None, ('bar',)))
    assert_equals(new.__doc__, 'doc')
