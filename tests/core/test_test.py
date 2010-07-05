# -*- coding: utf-8 -*-
"""
    test_test
    ~~~~~~~~

    Unittests for the unittests, sounds confusing?

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core.auth.models import User, UserProfile, Group


@refresh_database
def test_fixture_loader():
    data = [{'User': [{
        'username': u'ente',
        'email': u'some@one.com',
        'password': u'Booo!'
    }]}]
    # assert there's no such user yet
    eq_(User.query.filter_by(username=u'ente').count(), 0)

    # load the user into database
    FixtureLoader().from_list(db.session, data)
    user = User.query.filter_by(username=u'ente').first()
    assert_true(user)


@refresh_database
def test_fixture_references():
    data = [{
        'User': [{
            '&ente': {
                'username': u'ente',
                'email': u'some@one.com',
                'password': u'Boo!',
            }
        }]}, {
        'UserProfile': [{
            'user': '*ente',
            'real_name': u'Christopher Grebs',
            'website': u'http://webshox.org'
        }]
    }]
    # assert there's no such user yet
    eq_(User.query.filter_by(username=u'ente').count(), 0)

    # load the user and profile into database
    FixtureLoader().from_list(db.session, data)
    user = User.query.filter_by(username=u'ente').first()
    assert_true(user)
    eq_(user.profile.real_name, u'Christopher Grebs')
