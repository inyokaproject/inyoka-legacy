#-*- coding: utf-8 -*-
"""
    test_utils_collections
    ~~~~~~~~~~~~~~~~~~~~~~


    Some tests for testing all classes in `inyoka.utils.collections`.

    :copyright: 2008 by Christopher Grebs.
    :license: GNU GPL.
"""
from nose.tools import assert_raises
from inyoka.utils.collections import MultiMap


def test_map():
    map = MultiMap([('foo', 1), ('foo', 2), ('baaaz', 1), ('baaaz', 2)])
    assert map.keys() == ['baaaz', 'foo']
    assert map.items() == [('baaaz', [1, 2]), ('foo', [1, 2])]
    assert map.values() == [[1, 2], [1, 2]]
    map.clear()
    assert map.items() == []
    assert_raises(TypeError, map.pop)
