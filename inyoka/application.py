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

class Request(RequestBase):
    pass

class Response(ResponseBase):
    default_mimetype = 'text/html'

class InyokaApplication(object):

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
