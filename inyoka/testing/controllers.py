# -*- coding: utf-8 -*-
"""
    inyoka.testing.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~


    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import Response, IController, Rule, register, \
    render_template
from inyoka.core.auth import get_auth_system
from werkzeug import redirect


class TestingController(IController):
    name = 'testing'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/about', endpoint='about'),
        Rule('/user/<username>/', endpoint='profile'),
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
