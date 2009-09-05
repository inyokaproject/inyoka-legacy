from werkzeug.routing import Rule, EndpointPrefix

from inyoka.core.api import IController
from inyoka.core.controller import register
from inyoka.core.http import Response


class TestingController(IController):
    name = 'testing'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/about', endpoint='about'),
        Rule('/user/<username>/', endpoint='profile'),
    ]

    @register('index')
    def bla(self, request):
        return Response('apo')

    @register('profile')
    def user_profile(self, request, username):
        return Response('User %s existiert nicht' % username)
