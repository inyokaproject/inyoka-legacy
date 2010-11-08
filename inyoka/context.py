# -*- coding: utf-8 -*-
"""
    inyoka.context
    ~~~~~~~~~~~~~~

    Some internal definitions that should not be accessable by remote
    interfaces.  Those are exported by :mod:`inyoka.core.api`.

    Use the context locals with caution and only where
    you don't have access to the current request/application
    object at all.  If there are easy ways of *not* using
    thread locals, you should not use them.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from functools import partial
from werkzeug import LocalStack, LocalProxy, Local, LocalManager


def _lookup_object(name):
    """Lookup an object on the request stack.

    Returns either the object or raises an `RuntimeError` if we are
    not in an request context.
    """
    top = _request_ctx_stack.top
    if top is None:
        raise RuntimeError('working outside of request context')
    return getattr(top, name)


# Context Locals
# -------------
#
# Use these context locals with caution and only where
# you don't have access to the current request/application
# object at all.  If there are easy ways of *not* using
# context locals, you should not use them.

_request_ctx_stack = LocalStack()
local = Local()
local_manager = LocalManager(local)

# Proxy definitions of commonly used objects.
ctx = local('ctx')
request = LocalProxy(partial(_lookup_object, 'request'))


class LocalProperty(object):
    """Class/Instance property that returns something from the local stack.

    Note that if some value is not present in the current thread local
    it does *not* raise an `RuntimeError` but returns `None`.
    """

    def __init__(self, name):
        self.__name__ = name

    def __get__(self, obj, type=None):
        try:
            object = _lookup_object(self.__name__)
        except RuntimeError:
            object = None
        return object
