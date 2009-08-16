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
from werkzeug.routing import Map

from inyoka import setup_components
from .api import Controller

class Request(RequestBase):
    pass

class Response(ResponseBase):
    default_mimetype = 'text/html'

class InyokaApplication(object):
    def __init__(self):
        setup_components(['inyoka.testing.api.*'])
        self.url_map = Map(Controller.get_urlmap())

    def __call__(self, environ, start_response):
        """Make the application object a WSGI application."""

        request = Request(environ, self)

        try:
            response = Response('Hallo')
        except:
            raise

        # TODO: add session cleanup
        return ClosingIterator(response(environ, start_response),
                               [])

application = InyokaApplication()
