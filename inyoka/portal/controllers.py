#-*- coding: utf-8 -*-
"""
    inyoka.portal.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the portal app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IController, Rule, view, Response, \
    templated, href, redirect_to
from inyoka.core.auth import get_auth_system

class PortalController(IController):
    name = 'portal'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/login', endpoint='login'),
        Rule('/logout', endpoint='logout'),
        Rule('/register', endpoint='register'),
    ]

    @view('index')
    @templated('portal/index.html')
    def index(self, request):
        return { 'called_url': request.build_absolute_url(),
                 'link': href('portal/index') }

    @view('login')
    @templated('portal/login.html')
    def login(self, request):
        #return { 'login_form': form.as_widget() }
        return get_auth_system().login(request)

    @view('logout')
    def logout(self, request):
        get_auth_system().logout(request)
        return redirect_to('portal/index')

    @view('register')
    def register(self, request):
        return get_auth_system().register(request)


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
