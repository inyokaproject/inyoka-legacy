from inyoka.core.api import IController, register, Rule
from inyoka.core.http import Response
from inyoka.core.templating import render_template


class TestingController(IController):
    name = 'testing'

    url_rules = [
        Rule('/') > 'index',
        Rule('/about') > 'about',
        Rule('/user/<username>/') > 'profile',
    ]

    @register('index')
    def bla(self, request):
        print request.user
        return Response(render_template('testing.html', {'r': request}))

    @register('profile')
    def user_profile(self, request, username):
        return Response('User %s existiert nicht' % username)
