# -*- coding: utf-8 -*-
"""
    inyoka.news.search
    ~~~~~~~~~~~~~~~~~~

    Search provider of the news application.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import db, href
from inyoka.core.search import SearchProvider
from inyoka.news.models import Article


class NewsSearchProvider(SearchProvider):
    name = 'news'
    index = 'portal'
    _query = Article.query.options(db.eagerload(Article.author))

    def _prepare(self, article):
        return {
            'id': article.id,
            'title': article.title,
            'text': article.intro + article.text,
            'date': article.pub_date.date(),
            'author': article.author.username,
            'link': href(article),
            'tag': article.tags,
        }

    def prepare(self, ids):
        query = self._query.filter(Article.id.in_(ids))
        documents = {p.id: self._prepare(p) for p in query}
        for id, document in documents.iteritems():
            yield document

    def prepare_all(self):
        for article in db.select_blocks(self._query, Article.id):
            yield article.id, self._prepare(article)
