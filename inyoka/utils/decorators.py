# -*- coding: utf-8 -*-
"""
    inyoka.utils.decorators
    ~~~~~~~~~~~~~~~~~~~~~~~

    Decorators for every day usage.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import types
from inspect import getargspec
from functools import wraps, update_wrapper as _update_wrapper


_function_types = (types.FunctionType, types.MethodType)


def abstract(func):
    """Mark a method as abstract.  Throws a ``NotImplementedError``
    if an abstract method is called.

    Usage::

        >>> from inyoka import Interface
        >>> from inyoka.utils.decorators import abstract
        >>> class MyCoolNewInterface(Interface):
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

    @wraps(func)
    def wrapper(*__args, **__kw):
        raise NotImplementedError('Missing required %s() method' %\
                                  func.__name__)

    return wrapper


def update_wrapper(proxy, original):
    func = _update_wrapper(proxy, original)
    func.signature = getargspec(original)
    return func


def make_decorator(attr):
    """Return a method usable as a multifunctional decorator
    to make methods available under some alias.

    :param attr: A string determining what attribute will be set
                 to the alias value.
    """
    def _wrapper(func=None, alias=None):
        """Decorator to register `alias` to `func`."""
        def _proxy(func):
            if alias is None:
                setattr(func, attr, func.__name__)
            else:
                setattr(func, attr, alias)
            return func

        if isinstance(func, _function_types):
            # @register_view
            return update_wrapper(_proxy, func)(func)
        elif func is None:
            # @register_view()
            return _proxy
        elif isinstance(func, basestring):
            # @register_view('alias')
            alias = func
            return _proxy
    return _wrapper
