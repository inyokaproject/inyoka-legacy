# -*- coding: utf-8 -*-
"""
    inyoka.utils.decorators
    ~~~~~~~~~~~~~~~~~~~~~~~

    Decorators for every day usage.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
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

    def __get__(self, trash, type=None):
        if type is None:
            #TODO: I think we need to read some documentation what the
            #      arguments really are…
            raise RuntimeError('What happened?')
        value = self.func(type)
        setattr(type, self.__name__, value)
        return value
