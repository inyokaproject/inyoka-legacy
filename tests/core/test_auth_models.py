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


def test_user():
    me = User('me', 'me@example.com', 's3cr3t')
    db.session.commit()
    eq_(me._status, 0)
    eq_(me.status, USER_STATUS_MAP[0])
    assert_false(me.is_active)
    me.status = 'normal'
    eq_(USER_STATUS_MAP[me._status], me.status)
    assert_true(me.is_active)
    assert_true(me.profile is not None)
    assert_true(me is User.query.get('me'))
    assert_true(me is User.query.get(me.id))
    assert_true(me.check_password('s3cr3t'))
    assert_false(me.check_password('secret'))
    # and test if check_password hashing does work with unicode strings
    assert_true(me.check_password(u's3cr3t'))
    eq_(me.display_name, u'me')
    eq_(unicode(me), me.display_name)
    eq_(me.is_anonymous, False)

    # anonymous tests
    anon = User.query.get_anonymous()
    eq_(anon.username, ctx.cfg['anonymous_name'])


def test_groups():
    """Check that the self-referential many-to-many group relationship works"""
    g1 = Group(name='g1')
    g2 = Group(name='g2')
    g3 = Group(name='g3')
    g4 = Group(name='g4')
    db.session.commit()
    g1.children.update((g2, g3))
    g4.children.add(g2)
    g2.children.add(g3)
    db.session.commit()
    eq_(g1.children, set([g2, g3]))
    eq_(g4.children, set([g2]))
    eq_(g3.parents, set([g1, g2]))
