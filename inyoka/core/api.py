# -*- coding: utf-8 -*-
"""
    inyoka.core.api
    ~~~~~~~~~~~~~~~

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

# Imports for easy API access
from inyoka import Interface
from inyoka.core.context import ctx
from inyoka.core.database import db
from inyoka.core.http import Request, Response, redirect_to, redirect
from inyoka.core.routing import IController, IServiceProvider
from inyoka.core.routing import view, service, Rule, href
from inyoka.core.templating import templated, render_template
from inyoka.core.middlewares import IMiddleware
from inyoka.core.exceptions import *
from inyoka.core.cache import cache
from inyoka.core.serializer import SerializableObject
from inyoka.utils.logger import logger
from inyoka.i18n import *
