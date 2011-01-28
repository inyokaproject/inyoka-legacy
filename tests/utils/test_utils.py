# -*- coding: utf-8 -*-
"""
    test_utils
    ~~~~~~~~~~

    Unittests for various utilities.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from functools import partial
from inyoka.core.test import *
from inyoka.utils import classproperty


class Foo(object):
    bar = 'baz'

    @classproperty
    def bars(cls):
        return [cls.bar]


def test_classproperty():
    eq_(Foo.bar, 'baz')
    eq_(Foo.bars, ['baz'])
    Foo.bar = 'foo'
    eq_(Foo.bars, ['foo'])
