# -*- coding: utf-8 -*-
"""
    inyoka.core.services
    ~~~~~~~~~~~~~~~~~~~~

    Services for the core app.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.i18n import serve_javascript
from inyoka.core.api import IServiceProvider, Rule, service
from inyoka.core.models import Tag
from inyoka.core.auth.models import User


class CoreServiceController(IServiceProvider):
    component = 'core'

    url_rules = [
        Rule('/get_tags/', endpoint='get_tags'),
        Rule('/get_translations/', endpoint='get_translations'),
        Rule('/get_user/', endpoint='get_user'),
    ]

    #@service('get_tags', config={'core.tag': ['label', 'value'], 'show_type': False})
    @service('get_tags')
    def get_tags(self, request):
        q = request.args.get('q')
        if not q:
            tags = Tag.query.all()
        else:
            tags = Tag.query.filter(Tag.name.startswith(q))
        return [{
            'label': tag.name,
            'value': tag.id
        } for tag in tags[:10]]

    @service('get_user')
    def get_user(self, request):
        q = request.args.get('term')
        if not q:
            users = User.query.all()
        else:
            users = User.query.filter(User.username.startswith(q))
        return [user.username for user in users[:10]]

    @service('get_translations')
    def get_translations(self, request):
        return serve_javascript(request)
