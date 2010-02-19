# -*- coding: utf-8 -*-
"""
    inyoka.news.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the news app.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.l10n import get_month_names
from inyoka.core.api import IController, Rule, cache, view, templated, href
from inyoka.core.http import Response
from inyoka.news.models import Article, Category
from inyoka.utils.pagination import URLPagination


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
        months=get_month_names(),
        categories=categories,
        **data
    )


class NewsController(IController):
    name = 'news'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/<int:page>/', endpoint='index'),
        Rule('/<int:year>/<int:month>/', endpoint='index'),
        Rule('/<int:year>/<int:month>/<int:page>/', endpoint='index'),
        Rule('/category/<cslug>/', endpoint='index'),
        Rule('/category/<cslug>/<int:page>/', endpoint='index'),
        Rule('/<date:date>/<slug>/', endpoint='detail'),
#        Rule('/archive/', endpoint='archive'),
    ]

    @templated('news/index.html', modifier=context_modifier)
    @view('index')
    def index(self, request, year=None, month=None, cslug=None, page=1):
        category = None
        if year and month:
            articles = Article.query.by_date(year, month)
        elif cslug:
            category = Category.query.filter_by(slug=cslug).one()
            articles = category.articles
        else:
            articles = Article.query

        #TODO: add ACL for public articles
        articles = articles.order_by('-updated')

        pagination = URLPagination(articles, page=page, per_page=10)

        return {
            'articles':      pagination.get_objects(),
            'pagination':    pagination,
            'category':      category
        }

    @view('detail')
    def detail(self, request, date, slug):
        return Response('this is news entry %r from %s' % (slug, date.strftime('%F')))
