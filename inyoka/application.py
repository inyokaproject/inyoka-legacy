# -*- coding: utf-8 -*-
"""
    inyoka.application
    ~~~~~~~~~~~~~~~~~~

    The main WSGI application.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from time import time

from werkzeug import ClosingIterator, redirect
from sqlalchemy.exc import SQLAlchemyError

from inyoka.core.api import db, config, logger, IController, Request, \
    Response, IMiddleware
from inyoka.core.context import local, local_manager, current_request
from inyoka.core.http import DirectResponse
from inyoka.core.exceptions import HTTPException
from inyoka.core.routing import Map
from inyoka.core.config import config


class InyokaApplication(object):
    """The WSGI application that binds everything."""

    def __init__(self):
        self.config = config._get_current_object()
        self.bind()

        url_map = IController.get_urlmap() + IMiddleware.get_urlmap()
        self.url_map = Map(url_map)

    @property
    def url_adapter(self):
        domain = config['base_domain_name']
        try:
            adapter = self.url_map.bind_to_environ(
                current_request.environ,
                server_name=domain)
        except RuntimeError:
            adapter = self.url_map.bind(domain)
        return adapter

    def bind(self):
        """Bind the application to a thread local"""
        local.application = self
        local.config = self.config

    def dispatch_request(self, request):
        """Dispatch the request.

        This method tries to find the proper controller and view
        for the request path and does the request middleware wrapping
        as well.
        """
        try:
            urls = self.url_adapter
        except ValueError:
            # we cannot use make_full_domain() here because the url adapter
            # is used there too.  So we raise a new `ValueError` here too.
            # Thats why we do it the manual way
            return redirect('http://%s/' % config['base_domain_name'])

        for middleware in IMiddleware.iter_middlewares():
            response = middleware.process_request(request)

            if response is not None:
                return response

        # dispatch the request if not already done by some middleware
        try:
            rule, args = urls.match(request.path, return_rule=True)
            response = IController.get_view(rule.endpoint)(request, **args)
        except HTTPException, err:
            response = err.get_response(request)
        except SQLAlchemyError, err:
            db.session.rollback()
            logger.error(err)
            raise

        return response

    def dispatch_wsgi(self, environ, start_response):
        """Dispatch the request the WSGI way.

        This method binds the request, application and config to the
        current thread local and dispatches the request.
        It also wraps the response middleware processing and handles
        cookies.
        """
        # Create a new request object, register it with the application
        # and all the other stuff on the current thread but initialize
        # it afterwards.  We do this so that the request object can query
        # the database in the initialization method.
        self.bind()
        request = object.__new__(Request)
        local.request = request
        request.__init__(environ, self)

        try:
            response = self.dispatch_request(request)

            # force the response type to be a werkzeug response
            if isinstance(response, Response):
                response = Response.force_type(response, environ)
        except DirectResponse, exc:
            # a response type that works around the call with
            # (environ, start_response).  Use it with care and only
            # if there's no other way!
            # Some usage example is a middleware that needs to respond
            # directly to the client and needs to be sure that no other
            # middlewares can modify the response object what, generally
            # all middlewares can do in the common request-pipeline
            return exc.response

        # let middlewares process the response.  Note that we *only*
        # process the response object, if it's returned from some view.
        # If an request modifing middleware is in-place we never reach
        # this code block.
        for middleware in reversed(IMiddleware.iter_middlewares()):
            response = middleware.process_response(request, response)

        # apply common response processors like cookies and etags
        if request.session.should_save:
            # check for permanent session saving
            if request.session.get('_permanent_session'):
                max_age = 60 * 60 * 24 * 31 # one month
                expires = time() + max_age
            else:
                max_age = expires = None
            request.session.save_cookie(response, config['cookie_name'],
                max_age=max_age, expires=expires, httponly=True,
                domain=config['cookie_domain_name'])

        if response.status == 200:
            response.add_etag()
            response = response.make_conditional(request)

        return response(environ, start_response)

    def __call__(self, environ, start_response):
        """Make the application object a WSGI application."""
        return ClosingIterator(self.dispatch_wsgi(environ, start_response),
                               [db.session.close, local_manager.cleanup])
