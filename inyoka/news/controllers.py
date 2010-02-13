# -*- coding: utf-8 -*-
"""
    inyoka.news.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the news app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.l10n import get_month_names
from inyoka.core.api import IController, Rule, cache, view
from inyoka.core.http import Response
from inyoka.news.models import Article, Category


def context_modifier(request, context):
    """This function adds two things to the context of all pages:
    `archive`
        A list of the latest months with articles.
    `categories`
        A list of all categories.
    """
    key = 'news/archive'
    data = cache.get(key)
    if data is None:
        archive = Article.query.dates('pub_date', 'month')
        if len(archive) > 5:
            archive = archive[:5]
            short_archive = True
        else:
            short_archive = False
        data = {
            'archive':       archive,
            'short_archive': short_archive
        }
        cache.set(key, data)

    categories = Category.query.cached('news/categories')
    context.update(
        months=get_month_names()),
        categories=categories,
        **data
    )


class NewsController(IController):
    name = 'news'

    url_rules = [
        Rule('/', endpoint='index'),
#        Rule('/<int:page>/', endpoint='index'),
#        Rule('/<date:date>/', endpoint='index'),
#        Rule('/<date:date>/<int:page>/', endpoint='index'),
#        Rule('/category/<slug>/', endpoint='index'),
#        Rule('/category/<slug>/<int:page>/', endpoint='index'),
        Rule('/<date:date>/<slug>/', endpoint='detail'),
#        Rule('/archive/', endpoint='archive'),
    ]

    @view('index')
    def index(self, request):
        return Response('this is the news (aka ikhaya) index page')

    @view('detail')
    def detail(self, request, date, slug):
        return Response('this is news entry %r from %s' % (slug, date.strftime('%F')))
