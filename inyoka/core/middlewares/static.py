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
from werkzeug import SharedDataMiddleware
from werkzeug.routing import Rule

from inyoka.core import environ
from inyoka.core.context import config
from inyoka.core.middlewares import IMiddleware


STATIC_PATH = path.join(environ.PACKAGE_CONTENTS, config['static_path'])
MEDIA_PATH = path.join(environ.PACKAGE_CONTENTS, config['media_path'])
EXPORTS = {
    '/_static': STATIC_PATH,
    '/_media': MEDIA_PATH
}


class StaticMiddleware(IMiddleware, SharedDataMiddleware):
    """Handles static file requests and dispatches those requests
    to :cls:`werkzeug.SharedDataMiddleware`.
    """

    low_level = True

    priority = 99

    #TODO: make the urls configurable
    url_rules = [
        Rule('/_static', defaults={'file': '/'}, endpoint='static'),
        Rule('/_static/<path:file>', endpoint='static'),
        Rule('/_media', defaults={'file': '/'}, endpoint='media'),
        Rule('/_media/<path:file>', endpoint='media'),
    ]

    def __init__(self, ctx):
        IMiddleware.__init__(self, ctx)
        SharedDataMiddleware.__init__(self, self.application, EXPORTS)

    def __call__(self, *args, **kwargs):
        return SharedDataMiddleware.__call__(self, *args, **kwargs)
