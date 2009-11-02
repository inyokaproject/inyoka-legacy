#-*- coding: utf-8 -*-


# Imports for easy API access
from inyoka.core import environ
from inyoka.core.config import config
from inyoka.core.context import current_request, current_application
from inyoka.core.database import db
from inyoka.core.http import Request, Response
from inyoka.core.routing import IController, register, register_service, \
    Rule, href
from inyoka.utils.logger import logger
from inyoka.core.templating import templated, render_template
