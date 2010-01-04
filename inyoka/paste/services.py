# -*- coding: utf-8 -*-
"""
    inyoka.paste.services
    ~~~~~~~~~~~~~~~~~~~~~

    All service providers goes here.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import service, Rule, IServiceProvider
from inyoka.paste.models import Entry


class PasteServices(IServiceProvider):

    name = 'paste'

    url_rules = [
        Rule('/', endpoint='get_pastes'),
        Rule('/<int:limit>', endpoint='get_pastes'),
        Rule('/paste/<int:id>', endpoint='get_pastes')
    ]

    @service('get_pastes')
    def get_pastes(self, request, id=None, limit=10):
        if id is not None:
            return Entry.query.get(id)
        return Entry.query.limit(limit).all()
