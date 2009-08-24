from werkzeug.routing import Rule, EndpointPrefix

from inyoka.core.api import Controller, register

class TestingController(Controller):
    url_section = 'forum'
    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/about', endpoint='about')
    ]

    @register('index')
    def bla(self, request):
        return 'apo'        
