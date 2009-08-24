# -*- coding: utf-8 -*-
"""
    inyoka.application
    ~~~~~~~~~~~~~~~~~~

    The main WSGI application.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

from werkzeug import Request as RequestBase, Response as ResponseBase,\
                     ClosingIterator
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.routing import Map

from inyoka import setup_components
from inyoka.core.api import IController, IMiddleware

class Request(RequestBase):
    pass

class Response(ResponseBase):
    default_mimetype = 'text/html'

class InyokaApplication(object):
    def __init__(self):
        setup_components(['inyoka.testing.api.*'])
        self.url_map = Map(IController.get_urlmap())

    def handle_not_found(self, request, error):
        return error.get_response(request)

    def __call__(self, environ, start_response):
        """Make the application object a WSGI application."""

        request = Request(environ, self)
        response = None
        urls = self.url_map.bind_to_environ(environ)

        for middleware in IMiddleware.middlewares():
            response = middleware.process_request(request)
            if response is not None:
                break

        if response is None:
            try:
                try:
                    endpoint, args = urls.match()
                    response = IController.get_view(endpoint)(request, **args)
                except NotFound, e:
                    response = self.handle_not_found(request, e)

            except HTTPException, e:
                response = e.get_response(request)

        for middleware in reversed(IMiddleware.middlewares()):
            response = middleware.process_response(request, response)


        # TODO: add session cleanup
        return ClosingIterator(response(environ, start_response),
                               [])

application = InyokaApplication()
