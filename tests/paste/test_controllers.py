# -*- coding: utf-8 -*-
"""
    test_controllers
    ~~~~~~~~~~~~~~~~

    Unittests for the paste application.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.paste.controllers import PasteController


class TestPasteController(ViewTestCase):

    controller = PasteController

    def test_index(self):
        self.assertResponseOK(self.open('/'))
