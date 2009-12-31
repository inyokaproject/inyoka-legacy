# -*- coding: utf-8 -*-
"""
    inyoka.paste.services
    ~~~~~~~~~~~~~~~~~~~~~

    All service providers goes here.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from functools import partial
from inyoka.core.api import _, service, db, Rule, IServiceProvider
from inyoka.core.forms.utils import model_to_dict
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
        md = partial(model_to_dict, fields=('code', 'language', 'author_id', 'id'))
        if id is not None:
            return md(Entry.query.get(id))
        return [md(e) for e in Entry.query.limit(limit).all()]