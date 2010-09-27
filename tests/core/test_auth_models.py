# -*- coding: utf-8 -*-
"""
    test_auth_models
    ~~~~~~~~~~~~~~~~

    Tests for the core models and model mixins.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core.auth.models import User, USER_STATUS_MAP, Group


user_fixture = [{User: [{'username': u'me', 'email': u'me@example.com',
                         'password': u's3cr3t'}]}]

@with_fixtures(user_fixture)
def test_user(fixtures):
    me = fixtures['User'][0]
    db.session.commit()
    eq_(me._status, 0)
    eq_(me.status, USER_STATUS_MAP[0])
    assert_false(me.is_active)
    me.status = u'normal'
    eq_(USER_STATUS_MAP[me._status], me.status)
    assert_true(me.is_active)
    assert_true(me.profile is not None)
    assert_true(me is User.query.get(u'me'))
    assert_true(me is User.query.get(me.id))
    assert_true(me.check_password(u's3cr3t'))
    assert_false(me.check_password(u'secret'))
    # and test if check_password hashing does work with unicode strings
    assert_true(me.check_password(u's3cr3t'))
    eq_(me.display_name, u'me')
    eq_(unicode(me), me.display_name)
    eq_(me.is_anonymous, False)

    # check that anonymous is created no matter what happens ;)
    anon = User.query.get_anonymous()
    eq_(anon.username, ctx.cfg['anonymous_name'])

    me.deactivate()
    db.session.commit()
    assert_false(me.is_active)
    assert_true(me.profile is not None)
    eq_(USER_STATUS_MAP[3], me.status)

group_fixtures = [{Group: [
    {'&g1': {'name': 'g1'}},
    {'&g4': {'name': 'g4'}},
    {'&g2': {'name': 'g2', 'parents': set(['*g1', '*g4'])}},
    {'&g3': {'name': 'g3', 'parents': set(['*g1', '*g2'])}},
]}]


@with_fixtures(group_fixtures)
def test_groups(fixtures):
    """Check that the self-referential many-to-many group relationship works"""
    g1, g4, g2, g3 = fixtures['Group']
    eq_(g1.children, set([g2, g3]))
    eq_(g4.children, set([g2]))
    eq_(g3.parents, set([g1, g2]))
