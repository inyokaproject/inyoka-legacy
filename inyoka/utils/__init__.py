# -*- coding: utf-8 -*-
"""
    inyoka.utils
    ~~~~~~~~~~~~

    Various utilities.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from math import sqrt


def flatten_iterator(iter):
    """Flatten an iterator to one without any sub-elements"""
    for item in iter:
        if hasattr(item, '__iter__'):
            for sub in flatten_iterator(item):
                yield sub
        else:
            yield item


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


def getmembers(object, predicate=None, exclude_pattern=u'_'):
    """Return all members of an object as (name, value) pairs sorted by name.
    Optionally, only return members that satisfy a given predicate.

    If `exclude_pattern` is given all objects starting with that pattern
    wont be touched.
    """
    results = []
    for key in dir(object):
        if key.startswith(exclude_pattern):
            continue

        value = getattr(object, key)
        if not predicate or predicate(value):
            results.append((key, value))
    results.sort()
    return results
