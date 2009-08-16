from werkzeug.routing import Rule, EndpointPrefix

from inyoka.api import Controller

class TestingController(Controller):
    url_section = 'forum'
    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/about', endpoint='about')
    ]
    url_map = {
        'index': lambda x: 'index',
        'about': lambda x: 'about'
    }
