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

from inyoka.context import ctx, local_manager, _request_ctx_stack, _lookup_object
from inyoka.core.api import db, IController, Request, Response, \
    IMiddleware, IServiceProvider
from inyoka.core.exceptions import HTTPException, NotFound
from inyoka.core.routing import Map
from inyoka.utils.http import notfound


class _RequestContext(object):
    """The request context contains all request relevant information.  It is
    created at the beginning of the request and pushed to the
    `_request_ctx_stack` and removed at the end of it.  It will create the
    URL adapter and request object for the WSGI environment provided.
    """

    def __init__(self, ctx, environ):
        self.ctx = ctx
        self.request = request = ctx.dispatcher.request_class(environ)
        urls = ctx.dispatcher.get_url_adapter(environ)

        try:
            rule, args = urls.match(request.path, return_rule=True)
        except HTTPException as err:
            rule, args = None, None
            request.routing_exception = err
        request.url_rule = rule
        request.view_args = args

    def push(self):
        """Binds the request context."""
        _request_ctx_stack.push(self)

    def pop(self):
        """Pops the request context."""
        _request_ctx_stack.pop()

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        # do not pop the request stack if we are in debug mode and an
        # exception happened.  This will allow the debugger to still
        # access the request object in the interactive shell.  Furthermore
        # the context can be force kept alive for the test client.
        env = self.request.environ
        debug = self.ctx.cfg['debug']
        if not env.get('inyoka._preserve_context') and (tb is None or not debug):
            self.pop()


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

    def get_url_adapter(self, environ=None):
        """Get an url adapter.

        The adapter is bound to the current url map
        and, if present, the current request.
        """
        domain = self.ctx.cfg['base_domain_name']
        try:
            env = environ or ctx.current_request.environ
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
            # Test if we are on the correct base domain and do redirect
            # if we're using something like `localhost` instead.
            url_adapter = self.get_url_adapter(request.environ)
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
        request = _lookup_object('request')
        try:
            if request.routing_exception is not None:
                raise request.routing_exception

            try:
                view = self.get_view(request.endpoint)
                response = view(request, **request.view_args)
                if response is None:
                    raise ValueError('View function did not return a response')
            except db.NoResultFound:
                raise NotFound()

        except NotFound as err:
            if ctx.cfg['debug']:
                return notfound(request, url_adapter)
            response = err.get_response(request.environ)

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
        with self.request_context(environ) as reqctx:
            request = reqctx.request
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

    def request_context(self, environ):
        """Creates a request context from the given environment and binds
        it to the current context.  This must be used in combination with
        the `with` statement because the request is only bound to the
        current context for the duration of the `with` block.

        Example usage::

            with app.request_context(environ):
                do_something_with(request)

        The object returned can also be used without the `with` statement
        which is useful for working in the shell.  The example above is
        doing exactly the same as this code::

            ctx = app.request_context(environ)
            ctx.push()
            try:
                do_something_with(request)
            finally:
                ctx.pop()

        :param environ: a WSGI environment
        """
        return _RequestContext(self.ctx, environ)

    def test_request_context(self, *args, **kwargs):
        """Creates a WSGI environment from the given values (see
        :func:`werkzeug.create_environ` for more information, this
        function accepts the same arguments).
        """
        from werkzeug import create_environ
        return self.request_context(create_environ(*args, **kwargs))

    def __call__(self, environ, start_response):
        """The main dispatching interface of the Inyoka WSGI application.

        You shall not (never ever) access stuff like the db-session and locals
        in outer WSGI middlewares.  This method also keeps track of config
        changes and emits the proper `config-changed` signal.
        """
        try:
            # reload the configuration if it was changed
            if self.ctx.cfg.changed_external:
                self.ctx.cfg.reload()
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
