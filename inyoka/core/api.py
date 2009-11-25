#-*- coding: utf-8 -*-


# Imports for easy API access
from inyoka.core.context import current_request, current_application, config
from inyoka.core.database import db
from inyoka.core.http import Request, Response, redirect_to
from inyoka.core.routing import IController, view, service, Rule, href
from inyoka.core.templating import templated, render_template
from inyoka.core.middlewares import IMiddleware
from inyoka.core.exceptions import *
from inyoka.core import auth
from inyoka.utils.logger import logger
from inyoka.i18n import *


ctx = (type('Context', (object,), {
    'request': current_request,
    'application': current_application,
    'config': config
}))()
