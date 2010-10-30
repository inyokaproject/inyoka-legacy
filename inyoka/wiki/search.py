# -*- coding: utf-8 -*-
"""
    inyoka.wiki.search
    ~~~~~~~~~~~~~~~~~~

    Search provider of the wiki application.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import db, href
from inyoka.core.search import SearchProvider
from inyoka.wiki.models import Page, Revision
from inyoka.utils.xml import strip_tags


class WikiSearchProvider(SearchProvider):
    name = 'wiki'
    index = 'portal'
    _query = Page.query.options(db.eagerload(Page.current_revision,
        Revision.change_user, Revision.text))

    def _prepare(self, page):
        return {
            'id': page.id,
            'title': page.name,
            'text': strip_tags(page.current_revision.rendered_text),
            'date': page.current_revision.change_date.date(),
            'author': page.current_revision.change_user.username,
            'link': href(page),
        }

    def prepare(self, ids):
        query = self._query.filter(Page.id.in_(ids))
        d = dict((p.id, self._prepare(p)) for p in query)
        for id in ids:
            yield d[int(id)]

    def prepare_all(self):
        for page in db.select_blocks(self._query, Page.id):
            yield page.id, self._prepare(page)
