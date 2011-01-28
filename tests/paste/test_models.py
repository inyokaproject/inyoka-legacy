# -*- coding: utf-8 -*-
"""
    Test paste models

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core.auth.models import User
from inyoka.paste.models import PasteEntry



class TestEntryModel(DatabaseTestCase):

    fixtures = [
        {User: [{'&bob': {'username': 'bob', 'email': 'bob@example.com'}}]},
        {PasteEntry: [{'author': '*bob', 'text': 'void', 'title': u'some paste'},
                 {'author': '*bob', 'text': 'void'}]}
    ]

    def test_display_title(self):
        e1, e2 = self.data['PasteEntry']
        eq_(e1.display_title, 'some paste')
        eq_(e2.display_title, 'Paste #%d' % e2.id)
        eq_(unicode(e1), 'some paste')
        eq_(unicode(e2), 'Paste #%d' % e2.id)
