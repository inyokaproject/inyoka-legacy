# -*- coding: utf-8 -*-
"""
    inyoka.event.services
    ~~~~~~~~~~~~~~~~~~~~~

    All service providers goes here.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import service, Rule, IServiceProvider
from inyoka.event.models import Event


class EventServices(IServiceProvider):

    name = 'event'

    url_rules = [
        Rule('/', endpoint='get_events'),
        Rule('/<int:limit>', endpoint='get_events'),
        Rule('/event/<int:id>', endpoint='get_events')
    ]

    @service('get_events')
    def get_events(self, request, id=None, limit=10):
        if id is not None:
            return Event.query.get(id)
        return Event.query.limit(limit).all()
