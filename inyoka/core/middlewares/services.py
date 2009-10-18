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
#            return Response(json, content_type='application/json')
            return Response(json, content_type='text/plain')
