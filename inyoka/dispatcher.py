# -*- coding: utf-8 -*-
"""
    inyoka.dispatcher
    ~~~~~~~~~~~~~~~~~

    The main dispatching system.  This module handles various
    subsystems souch as url routing and dispatching as well
    as cleaning up various parts such as thread-locals after
    a request was successfully returned to the user.

    The dispatching system is wrapped by :class:`~inyoka.ApplicationContext`

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from time import time

from werkzeug import ClosingIterator, redirect, cached_property
from werkzeug.exceptions import NotFound

from inyoka.core.api import db, ctx, logger, IController, Request, \
    Response, IMiddleware, IServiceProvider
from inyoka.core.context import local, local_manager
from inyoka.core.exceptions import HTTPException
from inyoka.core.routing import Map



class RequestDispatcher(object):
    """The main dispatcher that handles all the dispatching and routing stuff."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.cleanup_callbacks = (db.session.close, local_manager.cleanup,
                                  self.ctx.bind)

    @cached_property
    def url_map(self):
        map = []
        for provider in (IController, IMiddleware, IServiceProvider):
            map.extend(provider.get_urlmap())
        return Map(map)

    @property
    def url_adapter(self):
        domain = self.ctx.cfg['base_domain_name']
        try:
            adapter = self.url_map.bind_to_environ(
                ctx.current_request.environ,
                server_name=domain)
        except AttributeError:
            adapter = self.url_map.bind(domain)
        return adapter

    def _get_callable(self, endpoint):
        for provider in (IController, IServiceProvider):
            try:
                return provider.get_callable_for_endpoint(endpoint)
            except:
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
            rule, args = urls.match(request.path, return_rule=True)
            response = self._get_callable(rule.endpoint)(request, **args)
        except HTTPException, err:
            response = err.get_response(request)
        except db.NoResultFound:
            response = NotFound().get_response(request)
        except db.SQLAlchemyError, err:
            db.session.rollback()
            logger.error(err)
            raise

        response = Response.force_type(response, environ)

        # let middlewares process the response.  Note that we *only*
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
        """
        # Create a new request object, register it with the application
        # and all the other stuff on the current thread but initialize
        # it afterwards.  We do this so that the request object can query
        # the database in the initialization method.
        self.ctx.bind()
        request = object.__new__(Request)
        local.request = request
        request.__init__(environ, self)

        response = self.dispatch_request(request, environ)

        # apply common response processors like cookies and etags
        if request.session.should_save:
            # check for permanent session saving
            if request.session.get('_permanent_session'):
                max_age = 60 * 60 * 24 * 31 # one month
                expires = time() + max_age
            else:
                max_age = expires = None
            request.session.save_cookie(response, ctx.cfg['cookie_name'],
                max_age=max_age, expires=expires, httponly=True,
                domain=ctx.cfg['cookie_domain_name'])

        if response.status == 200:
            response.add_etag()
            response = response.make_conditional(request)

        return response(environ, start_response)

    def __call__(self, environ, start_response):
        """The main dispatching interface of the Inyoka WSGI application."""
        return ClosingIterator(self.dispatch_wsgi(environ, start_response),
                               self.cleanup_callbacks)


def make_dispatcher(ctx):
    """Create the dispatcher object, wrap all middlewares and return
    it to the context.
    """
    dispatcher = RequestDispatcher(ctx)
    return dispatcher
