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
from inyoka.paste.models import PasteEntry


class TestPasteController(ViewTestCase):

    controller = PasteController

    def test_index(self):
        self.assertResponseOK(self.open('/'))
        self.assertTemplateUsed('paste/index.html')
        self.get_context_variable('form')

    def test_new_paste(self):
        self.assertResponseOK(self.open('/'))
        self.assertEqual(PasteEntry.query.filter_by(title=u'Test Paste').count(), 0)
        resp = self.submit_form('/', {'title': u'Test Paste',
                                      'text': u'This is a test paste',
                                      'language': 'text'})
        paste = PasteEntry.query.filter_by(title=u'Test Paste').first()
        self.assertNotEqual(paste, None)
        self.assertRedirects(resp, '/paste/%s/' % paste.id)
        self.assertEqual(PasteEntry.query.filter_by(title=u'Test Paste').count(), 1)
        db.session.delete(PasteEntry.query.filter_by(title=u'Test Paste').first())
        db.session.commit()
