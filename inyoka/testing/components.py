# -*- coding: utf-8 -*-
"""
    inyoka.testing.components
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Components for usage within tests.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sys, os
from operator import attrgetter
from inyoka.core.api import Response, IController, Rule, view, \
    render_template, config
from inyoka.core.auth import get_auth_system
from inyoka.core.subscriptions import SubscriptionType
from werkzeug import redirect


class TestingController(IController):
    name = 'testing'

    url_rules = [
    ]
