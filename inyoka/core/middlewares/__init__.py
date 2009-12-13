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
    __lazy_loading__ = True

    # cache for imported middlewares
    _middlewares = []

    # The higher the number the earlier the middleware will get called during
    # request, for the response, the result is reversed
    # TODO: maybe we need different orders for request and response
    # TODO: document sensible priority values
    priority = 0

    # A low level middleware will be handled just as ordinary wsgi
    # middlewares.  They are used to include external wsgi middlewares
    # into the inyoka core.  Note that you can still use the `UrlMixin`
    # features and any other middleware features for low level middlewares.
    # The only difference is that neither `process_request` nor
    # `process_response` is called but `__call__` with environ
    # and start_response as the arguments.
    # Note that your middleware *must* call the `self.application`
    # attribute if it does not return any data so that the request stack
    # can be continued.
    low_level = False

    # set `build_only` from `UrlMixin` to `True` 'cause middlewares should
    # never ever build matching url rules
    build_only = True

    def __init__(self, ctx):
        # bind the wsgi dispatcher to self.application so that the middleware
        # can on that
        self.application = ctx.application.dispatch_wsgi
        # then initialize the middleware with the global context module
        super(IMiddleware, self).__init__(ctx)
        # and bind the dispatcher to the middleware.  That way we get a
        # stacked request -> response pipeline
        ctx.application.dispatch_wsgi = self

    def process_request(self, request):
        pass

    def process_response(self, request, response):
        return response

    def __call__(self, environ, start_response):
        return self.application(environ, start_response)

    @classmethod
    def iter_middlewares(cls, low_level=False):
        if not cls._middlewares:
            cls._middlewares = sorted(
                cls.get_components(),
                key=lambda x: -x.priority)
        ret = cls._middlewares
        if low_level:
            ret = filter(lambda x: x.low_level, ret)
        return ret
