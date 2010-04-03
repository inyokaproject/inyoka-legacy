# -*- coding: utf-8 -*-
"""
    test_controllers
    ~~~~~~~~~~~~~~~~

    Unittests for the paste application.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import href, ctx
from inyoka.core.test import *
from inyoka.core.auth.models import User
from inyoka.paste.controllers import PasteController
from inyoka.paste.models import Entry


def get_data():
    author = User.query.first()
    return {
        'text': u"print 'hello world'",
        'language': 'python',
        'author': author
    }


class PasteTester(ViewTestSuite):

    controller = PasteController

    fixtures = {
        'pastes': [
            fixture(Entry, get_data)
    ]}
