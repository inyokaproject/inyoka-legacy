# -*- coding: utf-8 -*-
"""
    inyoka.portal.services
    ~~~~~~~~~~~~~~~~~~~~~~

    Services for the portal.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IServiceProvider, Rule, service
from inyoka.utils.text import get_random_password


class PortalServiceController(IServiceProvider):
    component = 'portal'

    url_rules = [
        Rule('/get_random_password/', endpoint='get_random_password'),
    ]

    @service('get_random_password')
    def get_random_password(self, request):
        return {'password': get_random_password()}
