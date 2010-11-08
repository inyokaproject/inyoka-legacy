# -*- coding: utf-8 -*-
"""
    inyoka.utils.datastructures
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Datastructures used to ease our life and to implement crucial
    parts of the :mod:`inyoka.markup` interface.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sys
from copy import deepcopy
from itertools import imap
from collections import namedtuple



#: Represents one token.
Token = namedtuple('Token', 'type value')


class _Missing(object):

    def __repr__(self):
        return 'no value'

    def __reduce__(self):
        return '_missing'

#: A singleton that represents missing values per thread
_missing = _Missing()
del _Missing


class BidiMap(dict):
    """
    A simpler API for simple Bidirectional Mappings.

    Example Usage::

        >>> map = BidiMap({1: 'dumb', 2: 'smartly', 3: 'clever'})
        >>> map[1]
        'dumb'
        >>> map['dumb']
        1

    :param items: A :class:`dict` like object where keys are integers.
    """

    def __init__(self, items=None):
        items = items or {}
        dict.__init__(self, **items)
        self.reversed = dict((v, k) for k, v in self.iteritems())
        if len(self) != len(self.reversed):
            raise ValueError('Values are not unique')

    def __getitem__(self, key):
        """
        Implement object[item] access to this class.
        """
        if isinstance(key, (int, long)):
            return dict.__getitem__(self, key)
        else:
            return self.reversed[key]

    def __repr__(self):
        return 'BidiMap(%s)' % dict.__repr__(self)


class TokenStreamIterator(object):
    """
    The iterator for tokenstreams.  Iterate over the stream
    until the eof token is reached.
    """

    def __init__(self, stream):
        self._stream = stream

    def __iter__(self):
        return self

    def next(self):
        token = self._stream.current
        if token.type == 'eof':
            raise StopIteration()
        self._stream.next()
        return token


class TokenStream(object):
    """
    A token stream wraps a generator and supports pushing tokens back.
    It also provides some functions to expect tokens and similar stuff.

    .. important::  Do never push more than one token back to the
                    stream.  Although the stream object won't stop you
                    from doing so, the behavior is undefined.  Multiple
                    pushed tokens are only used internally!

    The token stream is pickleable.  But note that if you pickle a stream, you
    get the exact copy after loading it but the original stream is lost
    since all items are rolled out.  This may be time-consuming on huge collections.
    """

    def __init__(self, generator):
        self._next = generator.next
        self._pushed = []
        self.current = Token('initial', '')
        self.next()

    @classmethod
    def from_tuple_iter(cls, tupleiter):
        """Create a new token stream from `tupleiter`"""
        return cls(Token(*a) for a in tupleiter)

    def __iter__(self):
        return TokenStreamIterator(self)

    def __getstate__(self):
        current = self.current
        pushed = self._pushed
        return {'items': list(self), 'current': current,
                'pushed': pushed}

    def __setstate__(self, state):
        self._next = iter(state['items']).next
        self._pushed = state['pushed']
        self.current = Token('initial', '')
        while self.current != state['current']:
            self.next()

    @property
    def eof(self):
        """Are we at the end of the tokenstream?"""
        return not bool(self._pushed) and self.current.type == 'eof'

    def debug(self, stream=None): #pragma: no cover
        """Displays the tokenized code on the stream provided or stdout."""
        if stream is None:
            stream = sys.stdout
        for token in self:
            stream.write(repr(token) + '\n')
            stream.flush()

    def look(self):
        """See what's the next token."""
        if self._pushed:
            return self._pushed[-1]
        old_token = self.current
        self.next()
        new_token = self.current
        self.current = old_token
        self.push(new_token)
        return new_token

    def push(self, token, current=False):
        """Push a token back to the stream (only one!)."""
        self._pushed.append(token)
        if current:
            self.next()

    def skip(self, num):
        """Got n tokens ahead."""
        for idx in xrange(num):
            self.next()

    def next(self):
        """Go one token ahead."""
        if self._pushed:
            self.current = self._pushed.pop()
        else:
            try:
                self.current = self._next()
            except StopIteration:
                if self.current.type != 'eof':
                    self.current = Token('eof', None)

    def expect(self, type, value=None):
        """expect a given token."""
        assert self.current.type == type
        if value is not None:
            assert self.current.value == value or \
                   (value.__class__ is tuple and
                    self.current.value in value)
        try:
            return self.current
        finally:
            self.next()

    def test(self, type, value=Ellipsis):
        """Test the current token."""
        return self.current.type == type and \
               (value is Ellipsis or self.current.value == value or
                value.__class__ is tuple and \
                self.current.value in value)

    def shift(self, token):
        """
        Push one token into the stream.
        """
        old_current = self.current
        self.next()
        self.push(self.current)
        self.push(old_current)
        self.push(token)
        self.next()


class OrderedDict(dict):
    """Simple ordered dict implementation.

    This implementation is based on the patch for insertion to py3k with some
    modifications based on other ordered dict implementations.
    Those do not change the py3k like interface.
    The OrderedDict got some more list-like functions as sort, index, byindex
    and such stuff.

    The constructor and :meth:`update()` both accept iterables of tuples as
    well as mappings:

    >>> d = OrderedDict([('a', 'b'), ('c', 'd')])
    >>> d.update({'foo': 'bar'})
    >>> d
    OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])

    Keep in mind that when updating from dict-literals the order is not
    preserved as these dicts are unsorted!

    You can copy an OrderedDict like a dict by using the constructor,
    :func:`copy.copy` or the :meth:`copy` method and make deep copies with
    :func:`copy.deepcopy`:

    >>> from copy import copy, deepcopy
    >>> copy(d)
    OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])
    >>> d.copy()
    OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])
    >>> OrderedDict(d)
    OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar')])
    >>> d['spam'] = []
    >>> d2 = deepcopy(d)
    >>> d2['spam'].append('eggs')
    >>> d
    OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar'), ('spam', [])])
    >>> d2
    OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar'), ('spam', ['eggs'])])

    All iteration methods as well as :meth:`keys`, :meth:`values` and
    :meth:`items` return the values ordered by the the time the key-value pair
    is inserted:

    >>> d.keys()
    ['a', 'c', 'foo', 'spam']
    >>> d.values()
    ['b', 'd', 'bar', []]
    >>> d.items()
    [('a', 'b'), ('c', 'd'), ('foo', 'bar'), ('spam', [])]
    >>> list(d.iterkeys())
    ['a', 'c', 'foo', 'spam']
    >>> list(d.itervalues())
    ['b', 'd', 'bar', []]
    >>> list(d.iteritems())
    [('a', 'b'), ('c', 'd'), ('foo', 'bar'), ('spam', [])]

    Index based lookup is supported too by :meth:`byindex` which returns the
    key/value pair for an index:

    >>> d.byindex(2)
    ('foo', 'bar')

    You can reverse the OrderedDict as well:

    >>> d.reverse()
    >>> d
    OrderedDict([('spam', []), ('foo', 'bar'), ('c', 'd'), ('a', 'b')])

    And sort it like a list:

    >>> d.sort(key=lambda x: x[0].lower())
    >>> d
    OrderedDict([('a', 'b'), ('c', 'd'), ('foo', 'bar'), ('spam', [])])

    For performance reasons the ordering is not taken into account when
    comparing two ordered dicts.
    """

    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        if not hasattr(self, '_keys'):
            self._keys = []
        self.update(*args, **kwds)

    def clear(self):
        """Clear the dictionary.  It's empty afterwards."""
        del self._keys[:]
        dict.clear(self)

    def __setitem__(self, key, value):
        if key not in self:
            self._keys.append(key)
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._keys.remove(key)

    def __iter__(self):
        """Iterate over all keys"""
        return iter(self._keys)
    iterkeys = __iter__

    def __reversed__(self):
        return reversed(self._keys)

    def reverse(self):
        """Reverse the keys in-place."""
        self._keys.reverse()

    def __deepcopy__(self, memo):
        d = memo.get(id(self), _missing)
        memo[id(self)] = d = self.__class__()
        dict.__init__(d, deepcopy(self.items(), memo))
        d._keys = self._keys[:]
        return d

    def copy(self):
        """Return a copy.
        The copy is no deepcopy, use :func:`copy.deepcopy` for that purpose.
        """
        return self.__class__(self)
    __copy__ = copy

    def __getstate__(self):
        return {'items': dict(self), 'keys': self._keys}

    def __setstate__(self, d):
        self._keys = d['keys']
        dict.update(self, d['items'])

    def popitem(self):
        """Return the most revent key-value pair."""
        if not self:
            raise KeyError('dictionary is empty')
        key = self._keys.pop()
        value = dict.pop(self, key)
        return key, value

    def keys(self):
        """Return all keys"""
        return self._keys

    def values(self):
        """Return all values"""
        return map(self.get, self._keys)

    def items(self):
        """Return key-value pairs"""
        return zip(self._keys, self.values())

    def itervalues(self):
        """Return an iterator that iterates over all values"""
        return imap(self.get, self._keys)

    def index(self, item):
        """Return the index used for `item`"""
        return self._keys.index(item)

    def byindex(self, index):
        """Access an item by index"""
        key = self._keys[index]
        return (key, dict.__getitem__(self, key))

    def pop(self, key, default=_missing):
        """Pop the value for `key` or raise :exc:`KeyError` if it's missing."""
        try:
            value = self[key]
        except KeyError:
            if default is _missing:
                raise
            return default
        else:
            del self[key]
            return value

    def update(self, other=(), **kwds):
        """Update the ordered dict.

        :param other: This can be either another :class:`dict`,
                      :class:`OrderedDict` or an iterable of tuples.
        """
        if isinstance(other, (dict, OrderedDict)):
            for key in other:
                self[key] = other[key]
        elif hasattr(other, "keys"):
            for key in other.keys():
                self[key] = other[key]
        else:
            for key, value in other:
                self[key] = value
        for key, value in kwds.items():
            self[key] = value

    def setdefault(self, key, default=None):
        """Set a default value for `key`"""
        try:
            return self[key]
        except KeyError:
            self[key] = default
        return default

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self.items()))

    @classmethod
    def fromkeys(cls, iterable, value=None):
        """Create a new ordered dict from `iterable` with default `value`"""
        d = cls()
        for key in iterable:
            d[key] = value
        return d

    def sort(self, cmp=None, key=None, reverse=False):
        """Sort the ordered dict in-place"""
        if key is not None:
            self._keys.sort(key=lambda k: key((k, self[k])))
        elif cmp is not None:
            self._keys.sort(lambda a, b: cmp((a, self[a]), (b, self[b])))
        else:
            self._keys.sort()
        if reverse:
            self._keys.reverse()
