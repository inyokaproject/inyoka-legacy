from inyoka.core.routing import IController, register, Rule
from inyoka.core.http import Response

from inyoka.core.auth import get_auth_system
from inyoka.core.templating import render_template
from werkzeug import redirect


class TestingController(IController):
    name = 'testing'

    url_rules = [
        Rule('/') > 'index',
        Rule('/about') > 'about',
        Rule('/user/<username>/') > 'profile',
    ]

    @register('index')
    def bla(self, request):
        if 'login' in request.args:
            get_auth_system().login(request, 'apollo13', 'apo')
            return redirect('/testing/')
        if 'logout' in request.args:
            get_auth_system().logout(request)
            return redirect('/testing/')
        return Response(render_template('testing.html', {}))

    @register('profile')
    def user_profile(self, request, username):
        return Response('User %s existiert nicht' % username)
