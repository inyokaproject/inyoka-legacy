# -*- coding: utf-8 -*-
"""
    inyoka.core.middlewares.static
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A middleware that integrates with werkzeug's SharedDataMiddleware and provides
    static file serving

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
from os.path import join
from werkzeug import SharedDataMiddleware
from werkzeug.routing import Rule

from inyoka.context import ctx
from inyoka.core.middlewares import IMiddleware


STATIC_PATH = join(os.environ['INYOKA_MODULE'], ctx.cfg['static_path'])
MEDIA_PATH = ctx.cfg['media_root']


class StaticMiddlewareBase(object):
    """Handles static file requests and dispatches those requests
    to :class:`werkzeug.SharedDataMiddleware`.

    This class represents the base implementation.  The concrete
    implementations are shown below.
    """
    low_level = True

    priority = 75

    exports = None

    build_only = True

    ignore_prefix = True

    def __init__(self, ctx):
        # Convert paths and ids to utf-8, otherwise werkzeug will break
        self.exports = dict(map(
            lambda x: (x[0].encode('utf-8'), x[1].encode('utf-8')),
            self.exports.items()))
        IMiddleware.__init__(self, ctx)
        SharedDataMiddleware.__init__(self, self.application, self.exports)

    def __call__(self, *args, **kwargs):
        return SharedDataMiddleware.__call__(self, *args, **kwargs)


class StaticMiddleware(StaticMiddlewareBase, IMiddleware, SharedDataMiddleware):
    """Concrete static file serving middleware implementation"""
    name = 'static'
    exports = {ctx.cfg['routing.urls.static'].split(':', 1)[1]: STATIC_PATH}
    url_rules = [
        Rule('/', defaults={'file': '/'}, endpoint='static'),
        Rule('/<path:file>', endpoint='static')
    ]


class MediaMiddleware(StaticMiddlewareBase, IMiddleware, SharedDataMiddleware):
    """Concrete media file serving middleware implementation"""
    name = 'media'
    exports = {ctx.cfg['routing.urls.media'].split(':', 1)[1]: MEDIA_PATH}
    url_rules = [
        Rule('/', defaults={'file': '/'}, endpoint='media'),
        Rule('/<path:file>', endpoint='media')
    ]
