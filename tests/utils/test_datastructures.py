# -*- coding: utf-8 -*-
"""
    test_datastructures
    ~~~~~~~~~~~~~~~~~~~

    Unittests for various datastructures implemented by inyoka.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import cPickle as pickle
import copy
from operator import itemgetter
from itertools import imap
from inyoka.core.test import *
from inyoka.utils.datastructures import BidiMap, TokenStream, TokenStreamIterator, \
    Token, _missing


def test_bidimap():
    map = BidiMap({
        1: 'dump',
        2: 'smartly',
        3: 'clever'
    })
    eq_(map[1], 'dump')
    eq_(map[2], 'smartly')
    eq_(map[3], 'clever')
    # and reversed
    eq_(map['dump'], 1)
    eq_(map['smartly'], 2)
    eq_(map['clever'], 3)


@raises(ValueError)
def test_bidimap_unique():
    map = BidiMap({
        1: 'maxorious',
        2: 'enteorious',
        3: 'barorious',
        4: 'barorious'
    })


def test_tokenstream():
    s = TokenStream(iter((Token('a', 1), Token('b', 2), Token('c', 3))))
    assert_equals(s.current, Token('a', 1))

    # from_tuple_iter
    s = TokenStream.from_tuple_iter(iter((('a', 1), ('b', 2), ('c', 3))))
    assert_equals(s.current, Token('a', 1))

    # iter
    assert_true(isinstance(iter(s), TokenStreamIterator))
    assert_equals(tuple(iter(s)), (Token('a', 1), Token('b', 2), Token('c', 3)))

    # eof
    s = TokenStream(iter((Token('a', 1), Token('b', 2), Token('c', 3))))
    assert_false(s.eof)
    list(s)
    assert_true(s.eof)

    # look, push
    s = TokenStream(iter((Token('a', 1), Token('b', 2), Token('c', 3))))
    assert_equals(s.current, Token('a', 1))
    assert_equals(s.look(), Token('b', 2))
    s.next()
    assert_equals(s.look(), Token('c', 3))
    s.push(Token('b', 2))
    assert_equals(s.look(), Token('b', 2))
    s.push(Token('e', 4), current=True)
    assert_equals(s.current, Token('e', 4))
    assert_equals(s.look(), Token('b', 2))

    # skip, next
    s = TokenStream(iter((Token('a', 1), Token('b', 2), Token('c', 3))))
    s.skip(1)
    assert_equals(s.current, Token('b', 2))
    s.next()
    assert_equals(s.current, Token('c', 3))
    s.push(Token('e', 4))
    assert_equals(s.current, Token('c', 3))
    s.next()
    assert_equals(s.current, Token('e', 4))
    s.next()
    assert_equals(s.current, Token('eof', None))

    # expect
    s = TokenStream(iter((Token('a', 1), Token('b', 2), Token('c', 3))))
    assert_equals(s.expect('a'), Token('a', 1))
    assert_equals(s.expect('b', 2), Token('b', 2))
    assert_raises(AssertionError, s.expect, 'e')
    assert_raises(AssertionError, s.expect, 'c', 5)

    # test
    s = TokenStream(iter((Token('a', 1), Token('b', 2), Token('c', 3))))
    assert_true(s.test('a'))
    s.next()
    assert_true(s.test('b', 2))

    # shift
    assert_equals(s.current, Token('b', 2))
    s.shift(Token('f', 5))
    assert_equals(s.current, Token('f', 5))
    s.next()
    assert_equals(s.current, Token('b', 2))


def test_tokenstream_picklable():
    import pickle
    s = TokenStream(iter((Token('a', 1), Token('b', 2), Token('c', 3))))
    assert_equals(s.current, Token('a', 1))
    s.next()
    assert_equals(s.current, Token('b', 2))
    dumped = pickle.dumps(s)
    loaded = pickle.loads(dumped)
    assert_equals(loaded.current, Token('b', 2))
    loaded.next()
    assert_equals(loaded.current, Token('c', 3))


def test_missing_picklable():
    assert_true(pickle.loads(pickle.dumps(_missing)) is _missing)
