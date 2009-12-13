# -*- coding: utf-8 -*-
"""
    inyoka.utils.datastructures
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Datastructures used to ease our life and to implement crutial
    parts of the `inyoka.markup` interface.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sys
from operator import itemgetter

class _Missing(object):

    def __repr__(self):
        return 'no value'

    def __reduce__(self):
        return '_missing'

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

    :param items: A `dict` like object where keys are integers.
    """

    def __init__(self, items=None):
        items = items or {}
        dict.__init__(self, **items)
        self.reversed = dict((v,k) for k, v in self.iteritems())
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


class Token(tuple):
    """
    Represents one token.
    """
    __slots__ = ()

    def __new__(self, type, value):
        return tuple.__new__(self, (intern(type), value))

    type = property(itemgetter(0))
    value = property(itemgetter(1))

    def __repr__(self):
        return 'Token(%r, %r)' % (
            self.type,
            self.value
        )


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

    Important note: Do never push more than one token back to the
                    stream.  Although the stream object won't stop you
                    from doing so, the behavior is undefined.  Multiple
                    pushed tokens are only used internally!
    """

    def __init__(self, generator):
        self._next = generator.next
        self._pushed = []
        self.current = Token('initial', '')
        self.next()

    @classmethod
    def from_tuple_iter(cls, tupleiter):
        return cls(Token(*a) for a in tupleiter)

    def __iter__(self):
        return TokenStreamIterator(self)

    @property
    def eof(self):
        """Are we at the end of the tokenstream?"""
        return not bool(self._pushed) and self.current.type == 'eof'

    def debug(self, stream=None):
        """Displays the tokenized code on the stream provided or stdout."""
        if stream is None:
            stream = sys.stdout
        for token in self:
            stream.write(repr(token) + '\n')

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

    def skip(self, n):
        """Got n tokens ahead."""
        for x in xrange(n):
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


# Based on the patch for insertion to py3k with some compatibility
# modifications

class OrderedDict(dict):

    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        if not hasattr(self, '_keys'):
            self._keys = []
        self.update(*args, **kwds)

    def clear(self):
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
        return iter(self._keys)

    def __reversed__(self):
        return reversed(self._keys)

    def popitem(self):
        if not self:
            raise KeyError('dictionary is empty')
        key = self._keys.pop()
        value = dict.pop(self, key)
        return key, value

    def __reduce__(self):
        items = [[k, self[k]] for k in self]
        inst_dict = vars(self).copy()
        inst_dict.pop('_keys', None)
        return (self.__class__, (items,), inst_dict)

    def keys(self):
        return self._keys

    def values(self):
        return map(self.get, self._keys)

    def items(self):
        return zip(self._keys, self.values())

    def pop(self, key, default=_missing):
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
        try:
            return self[key]
        except KeyError:
            self[key] = default
        return default

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self.items()))

    def copy(self):
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d

    def __eq__(self, other):
        if isinstance(other, OrderedDict):
            return len(self)==len(other) and \
                   all(p==q for p, q in zip(self.items(), other.items()))
        return dict.__eq__(self, other)
