#-*- coding: utf-8 -*-
"""
    test_utils_user
    ~~~~~~~~~~~~~~~

    Some tests for our user model.

    :copyright: 2008 by Christopher Grebs.
    :license: GNU GPL.
"""
from inyoka.portal.user import User
from inyoka.utils.user import gen_activation_key


def test_gen_activation_key():
    admin_user = User.objects.get(username='admin')
    assert gen_activation_key(admin_user) == '0ce3618156ca97b87f462c27af6099f7'
