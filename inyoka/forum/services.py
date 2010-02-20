# -*- coding: utf-8 -*-
"""
    inyoka.forum.services
    ~~~~~~~~~~~~~~~~~~~~~

    Services for the forum app.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.forum.models import Tag
from inyoka.core.api import IServiceProvider, Rule, service


class ForumServiceController(IServiceProvider):
    name = 'forum'

    url_rules = [
        Rule('/get_tags/', endpoint='get_tags'),
    ]

    @service('get_tags')
    def get_tags(self, request):
        q = request.args.get('q')
        if not q:
            tags = Tag.query.all()[:10]
        else:
            tags = Tag.query.filter(Tag.name.startswith(q))[:10]
        return tags
