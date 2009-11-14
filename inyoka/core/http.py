#-*- coding: utf-8 -*-
"""
    inyoka.core.http
    ~~~~~~~~~~~~~~~~

    This module implements various http helpers
    such as our own request and response classes.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import Request as BaseRequest, Response as BaseResponse, \
    redirect, get_current_url, cached_property
from werkzeug.contrib.securecookie import SecureCookie
from inyoka.core.context import config
from inyoka.core.routing import href


class Request(BaseRequest):

    def __init__(self, environ, application):
        self.application = application
        BaseRequest.__init__(self, environ)

    def build_absolute_url(self):
        return get_current_url(self.environ)

    @cached_property
    def session(self):
        return SecureCookie.load_cookie(self, secret_key=config['cookie_secret'])


class Response(BaseResponse):
    default_mimetype = 'text/html'


class DirectResponse(Exception):

    def __init__(self, response):
        Exception.__init__(self, response)
        self.message = 'direct response %r' % response
        self.response = response


def redirect_to(*args, **kwargs):
    """Temporarily redirect to an URL rule."""
    return redirect(href(*args, **kwargs))
