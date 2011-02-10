# -*- coding: utf-8 -*-
"""
    inyoka.utils
    ~~~~~~~~~~~~

    Various utilities.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""


def flatten_iterator(iter):
    """Flatten an iterator to one without any sub-elements"""
    for item in iter:
        if hasattr(item, '__iter__'):
            for sub in flatten_iterator(item):
                yield sub
        else:
            yield item


def flatten_list(iter):
    """Same as `flatten_iterator` but returns a list"""
    return list(flatten_iterator(iter))


class classproperty(object):
    """A mix of the built-in `classmethod` and `property`.

    This is used to achieve a property that is not bound to an instance.
    """

    def __init__(self, func, name=None):
        self.func = func
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__

    def __get__(self, desc, cls):
        value = self.func(cls)
        return value
