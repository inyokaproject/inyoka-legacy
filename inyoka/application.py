# -*- coding: utf-8 -*-
"""
    inyoka.application
    ~~~~~~~~~~~~~~~~~~

    The main WSGI application.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import ClosingIterator, redirect
from sqlalchemy.exc import SQLAlchemyError

from inyoka import setup_components
from inyoka.core.api import db, config, logger, IController, Request, \
    Response
from inyoka.core.context import local, local_manager
from inyoka.core.http import DirectResponse
from inyoka.core.exceptions import HTTPException
from inyoka.core.middlewares import IMiddleware
from inyoka.core.routing import DateConverter, Map


class InyokaApplication(object):
    """The WSGI application that binds everything."""

    def __init__(self):
        self.bind()
        #TODO: this should go into some kind of setup process
        if not config.exists:
            # write the inyoka.ini file
            trans = config.edit()
            trans.commit(force=True)
            config.touch()

        #TODO: utilize that!
        setup_components([
            'inyoka.testing.controllers.*',
            'inyoka.core.routing.*',
            'inyoka.core.auth.*',
            'inyoka.portal.controllers.*',
            'inyoka.news.controllers.*',
            'inyoka.forum.controllers.*',
            'inyoka.paste.controllers.*',
            'inyoka.core.middlewares.services.*',
            #'inyoka.core.middlewares.static.*',
        ])

        url_map = IController.get_urlmap() + IMiddleware.get_urlmap()
        self.url_map = Map(url_map)

    @property
    def url_adapter(self):
        domain = config['base_domain_name']
        if not local.request is None:
            adapter = self.url_map.bind_to_environ(
                local.request.environ,
                server_name=domain)
        else:
            adapter = self.url_map.bind(domain)
        return adapter

    def bind(self):
        """Bind the application to a thread local"""
        local.application = self

    def dispatch_request(self, request):
        try:
            urls = self.url_adapter
        except ValueError:
            return redirect('http://%s/' % config['base_domain_name'])

        for middleware in IMiddleware.iter_middlewares():
            response = middleware.process_request(request)

            if response is not None:
                return response

        # dispatch the request if not already done by some middleware
        try:
            rule, args = urls.match(request.path, return_rule=True)
            response = IController.get_view(rule.endpoint)(request, **args)
        except HTTPException, e:
            response = e.get_response(request)
        except SQLAlchemyError, e:
            db.session.rollback()
            logger.error(e)
            raise e

        return response

    def dispatch_wsgi(self, environ, start_response):
        # Create a new request object, register it with the application
        # and all the other stuff on the current thread but initialize
        # it afterwards.  We do this so that the request object can query
        # the database in the initialization method.
        request = object.__new__(Request)
        local.request = request
        self.bind()
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
            request.session.save_cookie(response)

        if response.status == 200:
            response.add_etag()
            response = response.make_conditional(request)

        return response(environ, start_response)

    def __call__(self, environ, start_response):
        """Make the application object a WSGI application."""
        return ClosingIterator(self.dispatch_wsgi(environ, start_response),
                               [local_manager.cleanup, db.session.close])


application = InyokaApplication()
