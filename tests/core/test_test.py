# -*- coding: utf-8 -*-
"""
    test_test
    ~~~~~~~~

    Unittests for the unittests, confused?

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core.test import flatten_data
from inyoka.core.auth.models import User, UserProfile, Group


@refresh_database
def test_fixture_loader_string_model_references():
    data = [{'User': [{
        'username': u'ente',
        'email': u'some@one.com',
        'password': u'Booo!'
    }]}]

    # assert there's no such user yet
    eq_(User.query.filter_by(username=u'ente').count(), 0)

    # load the user into database
    new_data = flatten_data(FixtureLoader().from_list(data))
    user = User.query.filter_by(username=u'ente').first()
    assert_true(user)
    assert_true(user is new_data['User'][0])
    eq_(len(new_data.keys()), 1)
    eq_(len(new_data['User']), 1)


@refresh_database
def test_fixture_loader_class_model_references():
    data = [{User: [{
        'username': u'ente',
        'email': u'some@one.com',
        'password': u'Boooo!'
    }]}]

    eq_(User.query.filter_by(username=u'ente').count(), 0)
    new_data = flatten_data(FixtureLoader().from_list(data))
    user = User.query.filter_by(username=u'ente').first()
    assert_true(user)
    assert_true(user is new_data['User'][0])
    eq_(len(new_data.keys()), 1)
    eq_(len(new_data['User']), 1)


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
    FixtureLoader().from_list(data)
    user = User.query.filter_by(username=u'ente').first()
    assert_true(user)
    eq_(user.profile.real_name, u'Christopher Grebs')
