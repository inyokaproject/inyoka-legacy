# -*- coding: utf-8 -*-
"""
    inyoka.news.search
    ~~~~~~~~~~~~~~~~~~

    Search provider of the news application.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import db, href
from inyoka.core.search import SearchProvider
from inyoka.news.models import Article
from inyoka.utils.xml import strip_tags


class NewsSearchProvider(SearchProvider):
    name = 'news'

    def _prepare(self, article):
        return {
            'id': article.id,
            'title': article.title,
            'text': strip_tags(article.rendered_intro + article.rendered_text),
            'date': article.pub_date.date(),
            'author': article.author.username,
            'link': href(article),
            'tag': article.tags,
        }

    def prepare(self, ids):
        query = Article.query.filter(Article.id.in_(ids)) \
                             .options(db.eagerload(Article.author))
        d = dict((a.id, self._prepare(a)) for a in query)
        for id in ids:
            yield d[int(id)]

    def prepare_all(self):
        query = Article.query.options(db.eagerload(Article.author))
        for article in db.select_blocks(query, Article.id):
            yield article.id, self._prepare(article)
