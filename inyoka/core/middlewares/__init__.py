from operator import attrgetter

from inyoka import Component

class IMiddleware(Component):
    # The higher the number the earlier the middleware will get called during
    # request, for the response, the result is reversed
    # TODO: maybe we need different orders for request and response
    # TODO: document sensible priority values
    priority = 0

    def process_request(self, request):
        pass

    def process_response(self, request, response):
        return response

    _middlewares = []
    @classmethod
    def middlewares(cls):
        if not cls._middlewares:
            _middlewares = sorted(cls.get_components(), key=attrgetter('priority'))
        return _middlewares

