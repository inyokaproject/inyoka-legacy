# -*- coding: utf-8 -*-
"""
    inyoka.dispatcher
    ~~~~~~~~~~~~~~~~~

    The main dispatching system.  This module handles various subsystems
    such as url-routing and dispatching as well as cleaning up various
    things like thread-locals after a request was successfully returned
    to the user.

    The dispatching system is wrapped by :class:`~inyoka.ApplicationContext`.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import timedelta, datetime

from werkzeug import redirect, cached_property

from inyoka.context import ctx, local_manager
from inyoka.core.api import db, IController, Request, Response, \
    IMiddleware, IServiceProvider, get_bound_request
from inyoka.core.exceptions import HTTPException, NotFound
from inyoka.core.routing import Map
from inyoka.utils.http import notfound


class RequestDispatcher(object):
    """The main dispatcher that handles all the dispatching
    and routing stuff.
    """

    #: Default class for requests.
    request_class = Request
    #: Default class for responses.
    response_class = Response

    def __init__(self, ctx):
        self.ctx = ctx
        self.cleanup_callbacks = (db.session.close, local_manager.cleanup,
                                  self.ctx.bind)

    @cached_property
    def url_map(self):
        """The url map collected from all url map providers.

        Those are:

            * :class:`~inyoka.core.routing.IController`
            * :class:`~inyoka.core.middlewares.IMiddleware`
            * :class:`~inyoka.core.routing.IServiceProvider`
        """
        map = []
        for provider in (IController, IMiddleware, IServiceProvider):
            map.extend(provider.get_urlmap())
        return Map(map)

    @property
    def url_adapter(self):
        """Get an url adapter.

        The adapter is bound to the current url map
        and, if present, the current request.
        """
        domain = self.ctx.cfg['base_domain_name']
        try:
            env = ctx.current_request.environ
            adapter = self.url_map.bind_to_environ(env, server_name=domain)
        except AttributeError:
            adapter = self.url_map.bind(domain)
        return adapter

    def get_view(self, endpoint):
        """Return a proper view for `endpoint`

        View providers must implement the `get_callable_for_endpoint`
        method.

        Those are (in execution-order):

            * :class:`~inyoka.core.routing.IController`
            * :class:`~inyoka.core.routing.IServiceProvider`
        """
        for provider in (IController, IServiceProvider):
            try:
                return provider.get_callable_for_endpoint(endpoint)
            except KeyError:
                continue
        raise

    def dispatch_request(self, request, environ):
        """Dispatch the request.

        This method tries to find the proper controller and view for the
        request and does the request/response middleware wrapping.
        """
        try:
            urls = self.url_adapter
        except ValueError:
            # we cannot use make_full_domain() here because the url adapter
            # is used there too.  So we raise a new `ValueError` here too.
            # Thats why we do it the manual way
            return redirect('http://%s/' % ctx.cfg['base_domain_name'])

        for middleware in IMiddleware.iter_middlewares():
            response = middleware.process_request(request)

            if response is not None:
                return response

        # dispatch the request if not already done by some middleware

        try:
            try:
                rule, args = urls.match(request.path, return_rule=True)
            except NotFound:
                return notfound(request, urls)

            request.endpoint = rule.endpoint

            try:
                response = self.get_view(rule.endpoint)(request, **args)
                if response is None:
                    raise ValueError('View function did not return a response')
            except db.NoResultFound:
                raise NotFound()

        except HTTPException as err:
            response = err.get_response(request.environ)

        response = self.make_response(request, response)

        # Let middlewares process the response.  Note that we *only*
        # process the response object, if it's returned from some view.
        # If an request modifing middleware is in-place we never reach
        # this code block.
        for middleware in reversed(IMiddleware.iter_middlewares()):
            response = middleware.process_response(request, response)

        return response

    def dispatch_wsgi(self, environ, start_response):
        """Dispatch the request the WSGI way.

        This method binds the request, application and config to the
        current thread local and dispatches the request.
        It handles cookies and etags.

        If you want to wrap the Inyoka dispatching process in some middleware
        but stay under the control of Inyoka you're best to wrap this method.

        See :attr:`~inyoka.core.middlewares.IMiddleware.application` as an
        example.
        """
        # Create a new request object, register it with the application
        # and all the other stuff on the current thread but initialize
        # it afterwards.  We do this so that the request object can query
        # the database in the initialization method.
        self.ctx.bind()
        request = get_bound_request(self.request_class, environ)

        response = self.dispatch_request(request, environ)

        # apply common response processors like cookies and etags
        if request.session.should_save:
            # check for permanent session saving
            expires = None
            if request.session.permanent:
                lifetime = timedelta(days=ctx.cfg['permanent_session_lifetime'])
                expires = datetime.utcnow() + lifetime

            request.session.save_cookie(response, ctx.cfg['cookie_name'],
                expires=expires, httponly=True,
                domain=ctx.cfg['cookie_domain_name'])

        if response.status == 200:
            response.add_etag()
            response = response.make_conditional(request)

        return response(environ, start_response)

    def make_response(self, request, rv):
        """Converts the return value from a handler to a real response
        object that is an instance of :attr:`response_class`.

        The following types are allowd for `rv`:

        ======================= ===========================================
        :attr:`response_class`  the object is returned unchanged
        :class:`str`            a response object is created with the
                                string as body
        :class:`unicode`        a response object is created with the
                                string encoded to utf-8 as body
        :class:`tuple`          the response object is created with the
                                contents of the tuple as arguments
        a WSGI function         the function is called as WSGI application
                                and buffered as response object
        ======================= ===========================================

        This method comes from `Flask <http://flask.pocoo.org>`_.

        :param request:
            A :class:`Request` instance.
        :param rv:
            The return value from the handler.
        :return:
            A :class:`Response` instance.
        """
        if isinstance(rv, self.response_class):
            return rv

        if isinstance(rv, basestring):
            return self.response_class(rv)

        if isinstance(rv, tuple):
            return self.response_class(*rv)

        if rv is None:
            raise ValueError('Handler did not return a response.')

        return self.response_class.force_type(rv, request.environ)

    def get_test_client(self):
        """Creates a test client for this application.

        :returns:
            A :class:`werkzeug.Client`, which is a :class:`Tipfy` wrapped
            for tests.
        """
        from werkzeug import Client
        return Client(self, self.response_class, use_cookies=True)

    def __call__(self, environ, start_response):
        """The main dispatching interface of the Inyoka WSGI application.

        You shall not (never ever) access stuff like the db-session and locals
        in outer WSGI middlewares.
        """
        try:
            return self.dispatch_wsgi(environ, start_response)
        finally:
            for callback in self.cleanup_callbacks:
                callback()


def make_dispatcher(ctx):
    """Create the dispatcher object, wrap all middlewares and return
    it to the context.
    """
    dispatcher = RequestDispatcher(ctx)
    return dispatcher
