#-*- coding: utf-8 -*-
"""
    portal/test_user
    ~~~~~~~~~~~~~~~~

    Some tests for our user model.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from os import path
import unittest
from datetime import datetime, timedelta
from StringIO import StringIO
from django.core import mail
from inyoka.conf import settings
from inyoka.portal.user import User, Group, UserProfile
from inyoka.utils.test import view, ViewTestCase, context, db



class TestUserModel(unittest.TestCase):

    def setUp(self):
        self.user = User.query.register_user('testing', 'example@example.com',
                                             'pwd', False)

    def test_automatic_profile_created(self):
        self.assertNotEqual(self.user.profile, None)
        self.assert_(isinstance(self.user.profile, UserProfile))

    def test_applied_profile_used(self):
        up = UserProfile(jabber='example@example.com')
        u = User.query.register_user('testing2', 'example2@example.com', 'pwd',
                                     False, profile=up)
        self.assertNotEqual(u.profile, None)
        self.assert_(isinstance(u.profile, UserProfile))
        self.assertEqual(u.profile.jabber, 'example@example.com')
        db.session.delete(u)
        db.session.commit()
        # assert that cascade rules are applied properly
        up = UserProfile.query.filter_by(jabber='example@example.com').first()
        self.assertEqual(up, None)

    def test_deactivation(self):
        self.user.deactivate()
        self.assert_(len(mail.outbox), 1)
        mail.outbox = []
        self.user = User.query.get(self.user.id)
        self.assertEqual(self.user.status, 3)

    def test_reactivation(self):
        result = self.user.reactivate('', '', datetime.utcnow())
        self.assert_('failed' in result)
        result = self.user.reactivate('', '', datetime.utcnow() - timedelta(days=34))
        self.assert_('failed' in result)
        self.user.status = 3
        db.session.commit()
        result = self.user.reactivate('example_new@example.com', 1,
                                      datetime.utcnow())
        self.assert_(len(mail.outbox), 1)
        mail.outbox = []
        self.assert_('success' in result)
        self.user = User.query.get(self.user.id)
        self.assertEqual(self.user.status, 1)

    def test_postcount(self):
        self.assertEqual(self.user.post_count, 0)
        self.user.inc_post_count()
        self.user = User.query.get(self.user.id)
        self.assertEqual(self.user.post_count, 1)

    def tearDown(self):
        db.session.delete(self.user)
        db.session.commit()


class TestGroupModel(unittest.TestCase):
    def setUp(self):
        self.group = Group(name='testing', is_public=True)
        db.session.add(self.group)
        db.session.commit()

    def test_icon(self):
        self.assertEqual(self.group.icon_url, None)
        icon = open(path.join(context.res_dir, 'group_icon_fit.png'))
        self.group.save_icon(icon)
        self.assertEqual(self.group.icon.path, path.join(settings.MEDIA_ROOT,
            'portal/team_icons/team_testing.png'))
        icon.close()

    def tearDown(self):
        db.session.delete(self.group)
        db.session.commit()
