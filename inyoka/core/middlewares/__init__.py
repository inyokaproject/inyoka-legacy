# -*- coding: utf-8 -*-
"""
    inyoka.core.middlewares
    ~~~~~~~~~~~~~~~~~~~~~~~

    Middlewares…

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka import Component
from inyoka.core.routing import UrlMixin


class IMiddleware(Component, UrlMixin):
    # cache for imported middlewares
    _middlewares = []

    # The higher the number the earlier the middleware will get called during
    # request, for the response, the result is reversed
    # TODO: maybe we need different orders for request and response
    # TODO: document sensible priority values
    priority = 0

    # set `build_only` from `UrlMixin` to `True` 'cause middlewares should
    # never ever build matching url rules
    build_only = True

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
