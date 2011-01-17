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
from collections import namedtuple


#: Represents one token.
Token = namedtuple('Token', ('type', 'value'))


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
        self.reversed = {v: k for k, v in self.iteritems()}
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
