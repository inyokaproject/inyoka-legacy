#-*- coding: utf-8 -*-
from werkzeug import Local, LocalManager, LocalProxy

# Thread Locals
# -------------
#
# Use these thread locals with caution and only where
# you don't have access to the current request/application
# object at all.  If there are easy ways of *not* using
# thread locals, you should not use them.
#
# NOTE: Never ever store custom values on `_local`!
#       Use some middleware that is able to store them
#       on a per-request way so that you are able to
#       clean them up.
_local = Local()
_local_manager = LocalManager(_local)

# the current request object.  This object is managed
# by _local_manager and cleaned up by the current :cls:`InyokaApplication`
# instance.
request = LocalProxy(_local, 'request')

# Imports for easy API access

from inyoka.core.controller import IController