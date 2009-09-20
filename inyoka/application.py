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
from inyoka.core.exceptions import HTTPException
from inyoka.core.http import Request, Response
from inyoka.core.database import db
#XXX
from inyoka.core.routing import config, DateConverter
from inyoka.utils.logger import logger


class InyokaApplication(object):
    """The WSGI application that binds everything."""

    def __init__(self):
        #TODO: this should go into some kind of setup process
        from inyoka.core.config import config
        if not config.exists:
            # write the inyoka.ini file
            trans = config.edit()
            trans.commit(force=True)
            config.touch()

        #TODO: utilize that!
        setup_components([
#            'inyoka.testing.api.*',
            'inyoka.core.routing.*',
            'inyoka.portal.controllers.*',
            'inyoka.news.controllers.*',
            'inyoka.forum.controllers.*',
        ])
        self.url_map = Map(IController.get_urlmap(),
            converters={
                'date': DateConverter,
        })
        self.url_adapter = self.url_map.bind(config['base_domain_name'])
        self.bind()

    def dispatch_request(self, request):
        """Dispatch a request.
        This includes url matching and a proper exception handling
        for HTTP or database errors.
        """
        # normal request dispatching
        urls = self.url_map.bind_to_environ(request.environ,
            server_name=config['base_domain_name'])
        self.url_adapter = urls

        try:
            endpoint, args = urls.match(request.path)
            response = IController.get_view(endpoint)(request, **args)
        except HTTPException, e:
            response = e.get_response(request)
        except SQLAlchemyError, e:
            db.session.rollback()
            logger.error(e)

        return response

    def dispatch(self, environ, start_response):
        """The overall dispatch process.
        This binds the current request to the thread locals,
        binds the current application instance too and dispatches
        to a proper view.
        """
        # Create a new request object, register it with the application
        # and all the other stuff on the current thread but initialize
        # it afterwards.  We do this so that the request object can query
        # the database in the initialization method.
        request = object.__new__(Request)
        _local.request = request
        self.bind()
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
        """Bind the application to a thread local"""
        _local.application = self

    def __call__(self, environ, start_response):
        """Make the application object a WSGI application."""
        return ClosingIterator(self.dispatch(environ, start_response),
                               [_local_manager.cleanup, db.session.close])


application = InyokaApplication()
