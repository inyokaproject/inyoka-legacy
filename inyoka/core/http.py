# -*- coding: utf-8 -*-
"""
    inyoka.core.http
    ~~~~~~~~~~~~~~~~

    This module implements various http helpers
    such as our own request and response classes.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import Request as BaseRequest, Response as BaseResponse, \
    redirect as _redirect, get_current_url, cached_property
from werkzeug.contrib.securecookie import SecureCookie
from inyoka.core.context import config
from inyoka.core.routing import href


class Request(BaseRequest):
    """Our Request object with some special attributes and methods.

    :param environ: The WSGI environ.
    :param application: The current application instance.

    """

    def __init__(self, environ, application):
        self.application = application
        BaseRequest.__init__(self, environ)

    def build_absolute_url(self):
        """Get the current absolute URL from the WSGI environ"""
        return get_current_url(self.environ)

    @cached_property
    def session(self):
        # hmac does not to support unicode values so we need to ensure
        # that we have a bytecode string here
        secret = config['cookie_secret'].encode('utf-8')
        name = config['cookie_name']
        return SecureCookie.load_cookie(self, name, secret_key=secret)


class Response(BaseResponse):
    """Our default response class with default mimetype to text/html"""
    default_mimetype = 'text/html'


class DirectResponse(Exception):
    """A :exc:`DirectResponse` is used to pass a response object
    to the user without executing any other routing or middleware
    dispatching.

    """

    def __init__(self, response):
        Exception.__init__(self, response)
        self.message = 'direct response %r' % response
        self.response = response


def redirect_to(*args, **kwargs):
    """Temporarily redirect to an URL rule."""
    return _redirect(href(*args, **kwargs))
