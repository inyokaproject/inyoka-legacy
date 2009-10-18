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
_local = Local()
_local_manager = LocalManager(_local)
current_request = _local('request')

def get_application():
    return getattr(_local, 'application', None)

# Imports for easy API access
from inyoka.core import environ
from inyoka.core.config import config
from inyoka.core.database import db
from inyoka.core.http import Request, Response
from inyoka.core.routing import IController, register, register_service, \
    Rule, href
from inyoka.utils.logger import logger
