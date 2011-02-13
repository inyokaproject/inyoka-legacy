# -*- coding: utf-8 -*-
"""
    test_auth_models
    ~~~~~~~~~~~~~~~~

    Tests for the core models and model mixins.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core.auth.models import User, USER_STATUS_MAP, Group


class TestUserModel(DatabaseTestCase):

    fixtures = [{User: [{u'username': u'me', u'email': u'me@example.com',
                         u'password': u's3cr3t'}]}]

    def test_user_status(self):
        me = self.data['User'][0]
        # test the numerical status value
        self.assertEqual(me._status, 0)
        # test that we are using the correct name for the status
        self.assertEqual(me.status, USER_STATUS_MAP[0])
        self.assertFalse(me.is_active)
        me.status = u'normal'
        self.assertEqual(me._status, 1)
        self.assertEqual(USER_STATUS_MAP[1], me.status)
        self.assertTrue(me.is_active)

    def test_automatic_user_profile(self):
        """Every user has an automatically created profile relation"""
        me = self.data['User'][0]
        self.assertTrue(me.profile is not None)

    def test_user_query_get(self):
        """User.query.get can either accept a username or id"""
        me = self.data['User'][0]
        self.assertTrue(me is User.query.get(u'me'))
        self.assertTrue(me is User.query.get(me.id))

    def test_user_password(self):
        me = self.data['User'][0]
        self.assertTrue(me.check_password(u's3cr3t'))
        self.assertFalse(me.check_password(u'secr3t'))
        self.assertFalse(me.check_password(u'„s€©®€™”'))

    def test_user_display_name(self):
        me = self.data['User'][0]
        self.assertEqual(me.display_name, u'me')
        self.assertEqual(unicode(me), me.display_name)

    def test_user_anonymous(self):
        me = self.data['User'][0]
        self.assertEqual(me.is_anonymous, False)
        # check that anonymous is created no matter what happens ;)
        anon = User.query.get_anonymous()
        self.assertEqual(anon.username, ctx.cfg['anonymous_name'])

    def test_user_deactivate(self):
        me = self.data['User'][0]
        me.deactivate()
        db.session.commit()
        self.assertFalse(me.is_active)
        self.assertTrue(me.profile is not None)
        self.assertEqual(USER_STATUS_MAP[3], me.status)



class TestGroupModel(DatabaseTestCase):
    fixtures = [{Group: [
        {'&g1': {'name': u'g1'}},
        {'&g4': {'name': u'g4'}},
        {'&g2': {'name': u'g2', 'parents': set(['*g1', '*g4'])}},
        {'&g3': {'name': u'g3', 'parents': set(['*g1', '*g2'])}},
    ]}]

    def test_groups(self):
        """Check that the self-referential many-to-many group relationship works"""
        g1, g4, g2, g3 = self.data['Group']
        self.assertEqual(g1.children, set([g2, g3]))
        self.assertEqual(g4.children, set([g2]))
        self.assertEqual(g3.parents, set([g1, g2]))
