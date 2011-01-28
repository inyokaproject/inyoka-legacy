# -*- coding: utf-8 -*-
"""
    inyoka.portal.search
    ~~~~~~~~~~~~~~~~~~~~

    Search index of the portal application.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from xappy import FieldActions
from inyoka.core.api import ctx
from inyoka.core.search import SearchIndex


class PortalSearchIndex(SearchIndex):
    name = 'portal'
    direct_search_allowed = ['tag', 'author', 'date']

    def _register_fields(self, indexer):
        lang = ctx.cfg['language']
        indexer.add_field_action('title', FieldActions.INDEX_FREETEXT, weight=5,
            language=lang)
        indexer.add_field_action('text', FieldActions.INDEX_FREETEXT,
            language=lang, spell=True)
        indexer.add_field_action('author', FieldActions.INDEX_EXACT)
        indexer.add_field_action('tag', FieldActions.INDEX_EXACT)
        indexer.add_field_action('date', FieldActions.SORTABLE, type='date')
