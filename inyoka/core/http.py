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
    CommonRequestDescriptorsMixin, CommonResponseDescriptorsMixin, \
    ResponseStreamMixin


class Request(BaseRequest):
    def __init__(self, environ, application):
        self.application = application
        BaseRequest.__init__(self, environ)


class Response(BaseResponse):
    default_mimetype = 'text/html'
