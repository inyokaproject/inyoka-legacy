# -*- coding: utf-8 -*-
"""
    inyoka.core.context
    ~~~~~~~~~~~~~~~~~~~

    Thread Locals

    Use these thread locals with caution and only where
    you don't have access to the current request/application
    object at all.  If there are easy ways of *not* using
    thread locals, you should not use them.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
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

current_request = local('request')
current_application = local('application')
config = local('config')

# import inyoka.core.config to setup the thread locals there
import inyoka.core.config
