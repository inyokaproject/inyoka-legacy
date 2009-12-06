# -*- coding: utf-8 -*-
"""
    inyoka.utils.datastructures
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Datastructures used for many things to avoid duplicate code.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""


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
