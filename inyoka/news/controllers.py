# -*- coding: utf-8 -*-
"""
    inyoka.news.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the news app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import _, IController, Rule, view
from inyoka.core.http import Response
from inyoka.admin.api import IAdminProvider


class NewsController(IController):
    name = 'news'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/<date:date>/<slug>/', endpoint='entry'),
    ]

    @view('index')
    def index(self, request):
        return Response('this is the news (aka ikhaya) index page')

    @view('entry')
    def entry(self, request, date, slug):
        return Response('this is news entry %r from %s' % (slug, date.strftime('%F')))
