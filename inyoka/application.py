# -*- coding: utf-8 -*-
"""
    inyoka.application
    ~~~~~~~~~~~~~~~~~~

    The main WSGI application.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import ClosingIterator
from werkzeug.routing import Map
from sqlalchemy.exc import SQLAlchemyError

from inyoka import setup_components
from inyoka.core.api import IController, _local, _local_manager
from inyoka.core.exceptions import HTTPException, NotFound, Forbidden
from inyoka.utils.http import Request, Response



class InyokaApplication(object):
    def __init__(self):
        #TODO: utilize that!
        setup_components(['inyoka.testing.api.*'])
        self.url_map = Map(IController.get_urlmap())
        self.url_adapter = None

    def dispatch_request(self, request):
        # normal request dispatching
        urls = self.url_map.bind_to_environ(request.environ)
        self.url_adapter = urls

        try:
            try:
                endpoint, args = urls.match(request.path)
                response = IController.get_view(endpoint)(request, **args)
            except NotFound, e:
                response = e.get_response(request)
            except Forbidden, e:
                #TODO: handle forbidden...
                pass
        except HTTPException, e:
            response = e.get_response(request)
        except SQLAlchemyError, e:
            #TODO: session rollback and logging!
            pass

        return response

    def dispatch(self, environ, start_response):
        # Create a new request object, register it with the application
        # and all the other stuff on the current thread but initialize
        # it afterwards.  We do this so that the request object can query
        # the database in the initialization method.
        request = object.__new__(Request)
        _local.request = request
        request.__init__(environ, self)

        # wrap the real dispatching in a try/except so that we can
        # intercept exceptions that happen in the application.
        # TODO: implement real exception handling
        try:
            response = self.dispatch_request(request)

            # make sure the response object is one of ours
            response = Response.force_type(response, environ)
        except:
            #TODO: exception handling!
            raise

        return response(environ, start_response)

    def bind(self):
        """bind the application to a thread local"""
        _local.application = self

    def __call__(self, environ, start_response):
        """Make the application object a WSGI application."""
        #TODO: database session cleanup
        return ClosingIterator(self.dispatch(environ, start_response),
                               [_local_manager.cleanup])


application = InyokaApplication()
