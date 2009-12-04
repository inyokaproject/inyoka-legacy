# -*- coding: utf-8 -*-
"""
    test_models
    ~~~~~~~~~~~~~~~

    Tests for the core models

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core.auth.models import User, USER_STATUS_MAP


def test_user_status():
    me = User('me', 'me@example.com', 's3cr3t')
    db.session.add(me)
    db.session.commit()
    eq_(me._status, 0)
    eq_(me.status, USER_STATUS_MAP[0])
    assert_false(me.is_active)
    me.status = 'normal'
    eq_(USER_STATUS_MAP[me._status], me.status)
    assert_true(me.is_active)
