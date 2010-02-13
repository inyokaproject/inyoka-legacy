# -*- coding: utf-8 -*-
"""
    inyoka.news.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the news app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IController, Rule, cache, view
from inyoka.core.http import Response
from inyoka.news.models import Article, Category



class NewsController(IController):
    name = 'news'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/<date:date>/<slug>/', endpoint='detail'),
    ]

    @view('index')
    def index(self, request):
        return Response('this is the news (aka ikhaya) index page')

    @view('detail')
    def entry(self, request, date, slug):
        return Response('this is news entry %r from %s' % (slug, date.strftime('%F')))
