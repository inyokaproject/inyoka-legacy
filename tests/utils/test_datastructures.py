# -*- coding: utf-8 -*-
"""
    test_datastructures
    ~~~~~~~~~~~~~~~~~~~

    Unittests for various datastructures implemented by inyoka.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import cPickle as pickle
from operator import itemgetter
from inyoka.core.test import *
from inyoka.utils.datastructures import BidiMap, OrderedDict, TokenStream, \
    TokenStreamIterator, Token


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


def test_ordereddict():
    # test dict inheritance
    d = OrderedDict()
    assert_true(isinstance(d, dict))

    # test various initialisation features
    assert_raises(TypeError, OrderedDict, 1, 3)

    items = [('a', 1), ('b', 2), ('c', 3), ('d', 4)]
    d = OrderedDict(items)

    # clear
    d.clear()
    assert_false('a' in d)
    assert_false('b' in d)

    # update
    d.update(items)
    assert_true('a' in d)
    assert_true('d' in d)

    # setitem
    d['e'] = 5
    assert_true('e' in d)

    # delitem
    del d['e']
    assert_false('e' in d)

    # iter
    assert_equals(list(d), ['a', 'b', 'c', 'd'])

    # reversed
    assert_equals(list(d.__reversed__()), ['d', 'c', 'b', 'a'])

    # popitem
    value = d.popitem()
    assert_equals(value, ('d', 4))
    d.clear()
    assert_raises(KeyError, d.popitem)
    d.update(items)

    # pickle support
    pickled = pickle.dumps(d)
    loaded = pickle.loads(pickled)
    assert_true(isinstance(loaded, OrderedDict))
    assert_equals(loaded, d)

    # keys, values, items
    assert_equals(d.keys(), ['a', 'b', 'c', 'd'])
    assert_equals(d.values(), [1, 2, 3, 4])
    assert_equals(d.items(), [('a', 1), ('b', 2), ('c', 3), ('d', 4)])

    # pop
    value = d.pop('d')
    assert_equals(value, 4)
    assert_raises(KeyError, d.pop, 'd')
    assert_equals(d.pop('d', 5), 5)

    # update
    d.update({'d': 4})
    assert_true('d' in d)
    d.update([('e', 5)])
    assert_true('e' in d)
    class DummyKeysIterator(object):
        def keys(self):
            return ['f']
        def __getitem__(self, key):
            return 6
    d.update(DummyKeysIterator())
    assert_true('f' in d)
    d.update({}, g=7)
    assert_true('g' in d)

    # setdefault
    assert_equals(d.setdefault('h', 8), 8)
    assert_true('h' in d)
    assert_equals(d.setdefault('h', 9), 8)

    # fromkeys, __eq__
    d.clear()
    d.update(items)
    nd = OrderedDict.fromkeys(('a', 'b', 'c', 'd'), 5)
    assert_equals({'a': 5, 'b': 5, 'c': 5, 'd': 5}, nd)
    assert_equals(d, dict(items))

    # index
    assert_equals(d.index('b'), 1)

    # sort
    nd.reverse()
    nd.sort()
    assert_equals(nd.items(), [('a', 5), ('b', 5), ('c', 5), ('d', 5)])

    d = OrderedDict([('a', 1), ('b', 2), ('c', 3), ('d', 4)])
    d.sort(key=itemgetter(1))
    assert_equals(d.items(), [('a', 1), ('b', 2), ('c', 3), ('d', 4)])
    d.sort(cmp=lambda a, b: cmp(b[1], a[1]))
    assert_equals(d.items(), [('d', 4), ('c', 3), ('b', 2), ('a', 1)])
    # sort does first sort and afterwards reverse the stuff, that's why we
    # get the same return value here.
    d.sort(reverse=True)
    assert_equals(d.items(), [('d', 4), ('c', 3), ('b', 2), ('a', 1)])
