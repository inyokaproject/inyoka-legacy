# -*- coding: utf-8 -*-
"""
    inyoka.core.services
    ~~~~~~~~~~~~~~~~~~~~

    Services for the core app.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.models import Tag
from inyoka.core.api import IServiceProvider, Rule, service


class CoreServiceController(IServiceProvider):
    component = 'core'

    url_rules = [
        Rule('/get_tags/', endpoint='get_tags'),
    ]

    @service('get_tags', config={'core.tag':['id', 'name'], 'show_type':False})
    def get_tags(self, request):
        q = request.args.get('q')
        if not q:
            tags = Tag.query.all()[:10]
        else:
            tags = Tag.query.filter(Tag.name.startswith(q))[:10]
        return tags
