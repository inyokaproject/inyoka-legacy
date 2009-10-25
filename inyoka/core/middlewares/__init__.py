# -*- coding: utf-8 -*-
"""
    inyoka.core.middlewares
    ~~~~~~~~~~~~~~~~~~~~~~~

    Middlewares…

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GPL, see LICENSE for more details.
"""
from inyoka import Component


class IMiddleware(Component):
    # cache for imported middlewares
    _middlewares = []


    # The higher the number the earlier the middleware will get called during
    # request, for the response, the result is reversed
    # TODO: maybe we need different orders for request and response
    # TODO: document sensible priority values
    priority = 0

    # if a middleware is applied as “low level” we apply environ and start_response
    # to :meth:`process_request` instead of the “high level” request object
    is_low_level = False

    def process_request(self, request):
        pass

    def process_response(self, request, response):
        return response

    @classmethod
    def iter_middlewares(cls):
        if not cls._middlewares:
            cls._middlewares = sorted(
                cls.get_components(),
                key=lambda x: -x.priority)
        return cls._middlewares
