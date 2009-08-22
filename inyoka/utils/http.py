#-*- coding: utf-8 -*-
"""
    inyoka.utils.http
    ~~~~~~~~~~~~~~~~~

    This module implements various http helpers
    such as our own request and response classes.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import BaseRequest, BaseResponse
from werkzeug import CommonRequestDescriptorsMixin, CommonResponseDescriptorsMixin, \
    ResponseStreamMixin


class Request(BaseRequest, CommonRequestDescriptorsMixin):
    pass


class Response(BaseResponse, CommonResponseDescriptorsMixin, ResponseStreamMixin):
    default_mimetype = 'text/html'
