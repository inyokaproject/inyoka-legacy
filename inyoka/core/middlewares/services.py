# -*- coding: utf-8 -*-
"""
    inyoka.core.middlewares.services
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A middleware that provides an “service” integration.

    What is a service?
    ------------------

    A service is some kind of special request handler that is used
    in ajax requests to provide a better user experience with
    richer and quicker user interfaces.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import simplejson
from werkzeug.exceptions import NotFound

from inyoka.core.api import Response
from inyoka.core.middlewares import IMiddleware
from inyoka.core.routing import IController


class ServiceMiddleware(IMiddleware):
    """
    Handles service requests (aka ajax requests)
    """

    priority = 99

    def process_request(self, request):
        if request.path == '/' and '__service__' in request.args:
            try:
                call = IController.get_servicemap()[request.args['__service__']]
            except KeyError:
                response = None
            else:
                response = call(request)

            if isinstance(response, Response):
                return response
            json = simplejson.dumps(response)
            return Response(json, content_type='application/json')
