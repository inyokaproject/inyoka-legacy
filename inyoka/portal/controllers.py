# -*- coding: utf-8 -*-
"""
    inyoka.portal.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the portal app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IController, Rule, view, Response, \
    templated, href, redirect_to, _
from inyoka.core.auth import get_auth_system
from inyoka.core.auth.models import User
from inyoka.utils.confirm import call_confirm, Expired


class PortalController(IController):
    name = 'portal'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/login/', endpoint='login'),
        Rule('/logout/', endpoint='logout'),
        Rule('/register/', endpoint='register'),
        Rule('/confirm/<key>/', endpoint='confirm'),
        Rule('/users/', endpoint='users'),
        Rule('/user/<username>/', endpoint='profile'),
    ]

    @view
    @templated('portal/index.html')
    def index(self, request):
        return {'called_url': request.current_url,
                 'link': href('portal/index')}

    @view
    @templated('portal/users.html')
    def users(self, request):
        return {'users': User.query}

    @view
    @templated('portal/profile.html')
    def profile(self, request, username):
        return {'user': User.query.get(username)}

    @view
    @templated('portal/login.html')
    def login(self, request):
        return get_auth_system().login(request)

    @view
    def logout(self, request):
        get_auth_system().logout(request)
        return redirect_to('portal/index')

    @view
    def register(self, request):
        return get_auth_system().register(request)

    @view
    def confirm(self, request, key):
        try:
            ret = call_confirm(key)
        except KeyError:
            ret = _('Key not found. Maybe it has already been used?'), False
        except Expired:
            ret = _('The supplied key is not valid anymore.'), False

        if isinstance(ret, tuple) and len(ret) == 2:
            # flash(*ret)
            # return redirect_to('portal/index')
            return Response('%s: %s' % (['success', 'fail'][not ret[1]],
                                        ret[0]), mimetype='text/plain')
        return ret



class CalendarController(IController):
    name = 'calendar'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/<date:date>/<slug>/', endpoint='entry'),
    ]

    @view('index')
    def index(self, request):
        return Response('this is calendar index page')

    @view('entry')
    def entry(self, request, date, slug):
        return Response('this is calendar entry %r from %r' % (slug, date))
