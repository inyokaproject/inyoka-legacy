# -*- coding: utf-8 -*-
"""
    inyoka.utils
    ~~~~~~~~~~~~

    Various utilities.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sys
from math import sqrt
from werkzeug import import_string


def flatten_iterator(iter):
    """Flatten an iterator to one without any sub-elements"""
    for item in iter:
        if hasattr(item, '__iter__'):
            for sub in flatten_iterator(item):
                yield sub
        else:
            yield item


# Algorithm taken from code.reddit.com by CondeNet, Inc.
def confidence(ups, downs):
    """Confidence sort, see
    http://www.evanmiller.org/how-not-to-sort-by-average-rating.html
    """
    n = float(ups + downs)
    if n == 0:
        return 0
    z = 1.0 #1.0 = 85%, 1.6 = 95%
    phat = float(ups) / n
    return sqrt(phat+z*z/(2*n)-z*((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n)


class classproperty(object):
    """
    A mix out of the built-in `classmethod` and
    `property` so that we can achieve a property
    that is not bound to an instance.

    Example::

        >>> class Foo(object):
        ...     bar = 'baz'
        ...
        ...     @classproperty
        ...     def bars(cls):
        ...         return [cls.bar]
        ...
        >>> Foo.bars
        ['baz']
    """

    def __init__(self, func, name=None):
        self.func = func
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__

    def __get__(self, desc, cls):
        value = self.func(cls)
        return value
