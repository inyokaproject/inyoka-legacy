from werkzeug.routing import Rule, EndpointPrefix

from inyoka.core.api import IController
from inyoka.core.controller import register
from inyoka.core.http import Response


class TestingController(IController):
    url_section = ''

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/about', endpoint='about')
    ]

    @register('index')
    def bla(self, request):
        return Response('apo')
