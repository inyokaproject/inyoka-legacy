#-*- coding: utf-8 -*-
"""
    pastebin/test_pastebin_models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Some tests for our pastebin models.


    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from os import path
import unittest
from inyoka.pastebin.models import Entry
from inyoka.utils.test import view, ViewTestCase, db
from inyoka.portal.user import User


class TestEntryModel(unittest.TestCase):
    """
    A class to test the Forum Model. At the moment we do not test the
    following methods :
    add_referrer
    get_absolute_url - we need a server
    """
    def setUp(self):
        """
        set up the test environment
        """
        self.user = User.query.register_user('test', 'ex@ex.com', 'pwd', False)
        self.entry = Entry(title = 'e1', lang = 'python',
                          code = 'ex', author = self.user)
        db.session.commit()

    def tearDown(self):
        db.session.delete(self.user)
        db.session.delete(self.entry)
        db.session.commit()

    def test_entry_creation(self):
        """
        test if the Entry model is created automatically
        """
        e = Entry.query.filter_by(id = self.entry.id).first()
        self.assertEqual(e, self.entry)

    def test_entry_methods(self):
        """
        test the methods of the Entry model
        """
        # TODO : we need to test the the highlighting a lil bit
        self.assertEqual(self.entry.code, 'ex')
        self.entry.set_code('abc')
        self.assertEqual(self.entry.code, 'abc')
        self.entry.code = 'def'
        self.assertEqual(self.entry.code, 'def')
        self.assertEqual(self.entry.referrer_list, [])
