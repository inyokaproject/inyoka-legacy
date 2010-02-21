# -*- coding: utf-8 -*-
"""
    inyoka.news.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the news app.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import date
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
        Rule('/category/<slug>/', endpoint='index'),
        Rule('/category/<slug>/<int:page>/', endpoint='index'),
        Rule('/<slug>/', endpoint='detail'),
        Rule('/archive/', endpoint='archive'),
        Rule('/archive/<int(fixed_digits=4):year>/', endpoint='archive'),
        Rule('/archive/<int(fixed_digits=4):year>/<int(fixed_digits=2):month>/',
             endpoint='archive'),
        Rule('/archive/<int(fixed_digits=4):year>/<int(fixed_digits=2):month>/'
             '<int(fixed_digits=2):day>/', endpoint='archive')
    ]

    @view('index')
    @templated('news/index.html', modifier=context_modifier)
    def index(self, request, slug=None, page=1):
        category = None
        if slug:
            category = Category.query.filter_by(slug=slug).one()
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
    def detail(self, request, slug):
        return Response('this is news entry %r' % slug)

    @view('archive')
    @templated('news/archive.html', modifier=context_modifier)
    def archive(self, request, year=None, month=None, day=None, page=1):
        if not year:
            ret = {
                'month_list': True,
                'articles': Article.query.dates('pub_date', 'month', dt_obj=True)
            }
            return ret

        url_args = dict(year=year, month=month, day=day)
        query = Article.query.published().by_date(year, month, day)
        pagination = URLPagination(query, page=page, per_page=15)

        ret = dict(year=year, month=month, day=day,
            date=date(year, month or 1, day or 1), month_list=False,
            pagination=pagination, articles=pagination.get_objects())
        return ret
