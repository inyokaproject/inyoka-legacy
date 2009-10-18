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
_local = Local()
_local_manager = LocalManager(_local)
current_request = _local('request')

def get_application():
    return getattr(_local, 'application', None)
