# -*- coding: utf-8 -*-
"""
    inyoka.core.middlewares
    ~~~~~~~~~~~~~~~~~~~~~~~

    Middlewares…

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka import Interface
from inyoka.core.context import ctx
from inyoka.core.routing import UrlMixin


class IMiddleware(Interface, UrlMixin):
    # cache for imported middlewares
    _middlewares = []

    # The higher the number the earlier the middleware will get called during
    # request, for the response, the result is reversed
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
        self.application = ctx.dispatcher.dispatch_wsgi
        # then initialize the middleware with the global context module
        super(IMiddleware, self).__init__(ctx)
        if self.low_level:
            # and bind the dispatcher to the middleware.  That way we get a
            # stacked request -> response pipeline
            ctx.dispatcher.dispatch_wsgi = self

    def process_request(self, request):
        """Process a request.

        If this method returns a response object no further dispatching
        will be continued and this response object is returned
        after some valididity checking.

        :param request: The actual request object to process.
        """
        pass

    def process_response(self, request, response):
        """Process the response object.

        This method must return a valid response object.
        """
        return response

    def __call__(self, environ, start_response):
        return self.application(environ, start_response)

    @classmethod
    def iter_middlewares(cls):
        """Return all middlewares ordered by priority."""
        if not cls._middlewares:
            cls._middlewares = sorted(
                ctx.get_implementations(cls, instances=True),
                key=lambda x: -x.priority)
        ret = cls._middlewares
        return ret


class CommonMiddleware(IMiddleware):
    """A common middleware that implements various features commonly required
    to get the inyoka core work properly.

    Currently it takes care of:

     * Prevent HTTP-Cache if flashed messages are present in the current session.

    """

    def process_response(self, request, response):
        if request.has_flashed_messages():
            response.prevent_caching()
        return response
