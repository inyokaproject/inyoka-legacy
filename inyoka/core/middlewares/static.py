# -*- coding: utf-8 -*-
"""
    inyoka.core.middlewares.static
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A middleware that integrates with werkzeug's SharedDataMiddleware and provides
    static file serving

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from os import path
import simplejson
from werkzeug import SharedDataMiddleware
from werkzeug.routing import Rule
from werkzeug.exceptions import NotFound

from inyoka.core import environ
from inyoka.core.middlewares import IMiddleware
from inyoka.core.config import config


STATIC_PATH = path.join(environ.PACKAGE_CONTENTS, config['static_path'])
MEDIA_PATH = path.join(environ.PACKAGE_CONTENTS, config['media_path'])



class StaticMiddleware(IMiddleware, SharedDataMiddleware):
    """Handles static file requests and dispatches those requests
    to :cls:`werkzeug.SharedDataMiddleware`.
    """

    priority = 99

    is_low_level = True

    url_rules = [
        Rule('/__static__', defaults={'file': '/'}, endpoint='static/file'),
        Rule('/__static__/<path:file>', endpoint='static/file'),
        Rule('/__media__', defaults={'file': '/'}, endpoint='media/file'),
        Rule('/__media__/<path:file>', endpoint='media/file'),
    ]

    def __init__(self, *args, **kwargs):
        app = lambda e, s: None
        exports = {
            '/__static__': STATIC_PATH,
            '/__media__': MEDIA_PATH
        }
        SharedDataMiddleware.__init__(self, app, exports)

    def process_request(self, environ, start_response):
        return self(environ, start_response)
