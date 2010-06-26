# -*- coding: utf-8 -*-
"""
    inyoka.context
    ~~~~~~~~~~~~~~

    Thread Locals

    Use these thread locals with caution and only where
    you don't have access to the current request/application
    object at all.  If there are easy ways of *not* using
    thread locals, you should not use them.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

from werkzeug import Local, LocalManager

# Thread Locals
# -------------
#
# Use these thread locals with caution and only where
# you don't have access to the current request/application
# object at all.  If there are easy ways of *not* using
# thread locals, you should not use them.
#
# Please also note that you should *ever* set the `local` proxy
# values to `None` before initializing the proxy.  This adds some
# proper “not defined” manner by returning `None` instead of raising
# an RuntimeException
#
local = Local()
local_manager = LocalManager(local)

ctx = local('ctx')
request = local('request')


class LocalProperty(object):
    """Class/Instance property that returns something from the local.

    Note that if some value is not present in the current thread local
    it does *not* raise an AttributeError but returns `None`.
    """

    def __init__(self, name):
        self.__name__ = name

    def __get__(self, obj, type=None):
        return getattr(local, self.__name__, None)
