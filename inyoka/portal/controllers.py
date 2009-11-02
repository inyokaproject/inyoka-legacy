#-*- coding: utf-8 -*-
"""
    inyoka.portal.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the portal app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IController, Rule, register, register_service, \
    href, Response, templated


class PortalController(IController):
    name = 'portal'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/user/<username>/', endpoint='user_profile'),
    ]

    @register('index')
    @templated('portal/index.html')
    def index(self, request):
        return { 'called_url': request.build_absolute_url(),
                 'link': href('portal/index') }

    @register('user_profile')
    def user_profile(self, request, username):
        return Response('this is user %s' % username)

    @register_service('userlist')
    def userlist(self, request):
        return ['ich', 'du', u'Müllers Kuh']


class CalendarController(IController):
    name = 'calendar'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/<date:date>/<slug>/', endpoint='entry'),
    ]

    @register('index')
    def index(self, request):
        return Response('this is calendar index page')

    @register('entry')
    def entry(self, request, date, slug):
        return Response('this is calendar entry %r from %r' % (slug, date))
