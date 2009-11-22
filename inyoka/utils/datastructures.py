# -*- coding: utf-8 -*-
"""
    inyoka.core.datastructures
    ~~~~~~~~~~~~~~~~~~

    Datastructures used for many Things to avoid duplicate code.

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

    """

    def __init__(self, items=None):
        """
        Constructor

        items must be a Dict like Object, where keys are Integers.
        """
        items = items or {}
        dict.__init__(self, **items)
        self.reversed = dict((v,k) for k, v in self.iteritems())

    def __getitem__(self, key):
        """
        Implement object[item] Access to this Class.
        """
        if isinstance(key, int):
            return dict.__getitem__(self, key)
        else:
            return self.reversed[key]
