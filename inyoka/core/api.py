# -*- coding: utf-8 -*-
"""
    inyoka.core.api
    ~~~~~~~~~~~~~~~

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

# Imports for easy API access
from inyoka import Component
from inyoka.core.context import request as current_request, ctx
from inyoka.core.database import db
from inyoka.core.http import Request, Response, redirect_to
from inyoka.core.routing import IController, view, service, Rule, href
from inyoka.core.templating import templated, render_template
from inyoka.core.middlewares import IMiddleware
from inyoka.core.exceptions import *
from inyoka.core.cache import cache
from inyoka.core import auth
from inyoka.core import markup
from inyoka.utils.logger import logger
from inyoka.i18n import *
