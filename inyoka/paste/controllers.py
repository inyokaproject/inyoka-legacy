#-*- coding: utf-8 -*-
"""
    inyoka.paste.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the paste app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IController, Rule, register, register_service, \
    href, Response, templated


class PasteController(IController):
    name = 'paste'

    url_rules = [
        Rule('/') > 'index',
    ]


    @register('index')
    @templated('paste/index.html')
    def index(self, request):
        return {
            'value': request.args.get('value', 'nix'),
        }
