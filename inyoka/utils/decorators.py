# -*- coding: utf-8 -*-
"""
    inyoka.utils.decorators
    ~~~~~~~~~~~~~~~~~~~~~~~

    Some decorators and utilities for using decorators.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""


def abstract(func):
    """Mark a method as abstract.  Throws a ``NotImplementedError``
    if an abstract method is called.

    Usage::

        >>> from inyoka import Component
        >>> from inyoka.utils.decorators import abstract
        >>> class MyCoolNewInterface(Component):
        ...     '''Some interface that only implements the interface'''
        ...
        ...     @abstract
        ...     def push_me(self):
        ...         '''You can write some documentation here if you like to'''
        ...
        >>> class NotReallyConcrete(MyCoolNewInterface):
        ...     # this class does not define `push_me`
        ...     pass
        ...
        >>> obj = NotReallyConcrete()
        >>> obj.push_me()
        Traceback (most recent call last):
        ...
        NotImplementedError: Missing required push_me() method

    """

    def wrapper(*__args, **__kw):
        raise NotImplementedError('Missing required %s() method' %\
                                  func.__name__)
    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__
    return wrapper
