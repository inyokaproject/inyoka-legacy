# -*- coding: utf-8 -*-
"""
    test_mail
    ~~~~~~~~~

    Unittests for our email framework and utilities.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core import mail


class TestMailFramework(TestCase):

    def setUp(self):
        self._configured_log = ctx.cfg['email.log_only']
        self._configured_from = ctx.cfg['email.system_email']
        self._configured_website = ctx.cfg['website_title']
        ctx.cfg['email.log_only'] = True
        ctx.cfg['email.system_email'] = 'system@inyokaproject.org'
        ctx.cfg['website_title'] = 'Test System'

    def tearDown(self):
        ctx.cfg['email.log_only'] = self._configured_log
        ctx.cfg['email.system_email'] = self._configured_from
        ctx.cfg['website_title'] = self._configured_website

    def test_split_email(self):
        self.assertEqual(mail.split_email(u'John Doe'), (u'John Doe', None))
        self.assertEqual(mail.split_email(u'John Doe <john@doe.com>'), (u'John Doe', u'john@doe.com'))
        self.assertEqual(mail.split_email(u'john@doe.com'), (None, u'john@doe.com'))

    def test_send_email(self):
        mail.send_email(u'Test', u'Text', 'info@inyokaproject.org', False)
        expected = '''\
MIME-Version: 1.0
From: Test System <system@inyokaproject.org>
To: info@inyokaproject.org
Subject: Test
Content-Transfer-Encoding: 8bit
Content-Type: text/plain; charset=utf-8

Text'''
        self.assertEqual(mail.outbox[0], expected)

    def test_send_email_quite(self):
        # does not raise any exception
        ctx.cfg['email.log_only'] = False
        mail.send_email(u'Test', u'Text', 'info@inyokaproject.org', True)
