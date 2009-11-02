# -*- coding: utf-8 -*-
"""
    inyoka.testing.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~


    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import Response, IController, Rule, register, \
    render_template
from inyoka.core.auth import get_auth_system
from werkzeug import redirect


class TestingController(IController):
    name = 'testing'

    url_rules = [
    ]
