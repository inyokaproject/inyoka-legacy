#-*- coding: utf-8 -*-
"""
    inyoka.portal.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the portal app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IController, Rule, register
from inyoka.core.http import Response


class PortalController(IController):
    name = 'portal'

    url_rules = [
        Rule('/') > 'index',
        Rule('/user/<username>/') > 'user_profile',
    ]

    @register('index')
    def index(self, request):
        return Response('this is the portal index page')

    @register('user_profile')
    def user_profile(self, request, username):
        return Response('this is user %s' % username)


class CalendarController(IController):
    name = 'calendar'

    url_rules = [
        Rule('/') > 'index',
        Rule('/<date:date>/<slug>/') > 'entry',
    ]

    @register('index')
    def index(self, request):
        return Response('this is calendar index page')

    @register('entry')
    def entry(self, request, date, slug):
        return Response('this is calendar entry %r from %r' % (slug, date))

