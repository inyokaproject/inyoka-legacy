#-*- coding: utf-8 -*-
"""
    inyoka.news.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the news app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IController, Rule, register
from inyoka.utils.http import Response

class NewsController(IController):
    name = 'news'

    url_rules = [
        Rule('/') > 'index',
        Rule('/<int(fixed_digits=4,min=0):year>/<int(fixed_digits=2,min=0):month>/<int(fixed_digits=2,min=0):day>/<slug>/') > 'entry',
    ]

    @register('index')
    def index(self, request):
        return Response('this is the news (aka ikhaya) index page')

    @register('entry')
    def entry(self, request, year, month, day, slug):
        return Response('this is news entry %r from %d-%d-%d' % (slug, year, month, day))
