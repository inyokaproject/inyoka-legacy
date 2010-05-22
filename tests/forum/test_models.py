# -*- coding: utf-8 -*-
"""
    Test forum models

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core.models import Tag
from inyoka.core.auth.models import User
from inyoka.forum.models import Question, Answer, Forum, Vote


def get_user_callback():
    return User.query.get('anonymous')


class TestForumApplication(TestSuite):

    fixtures = {
        'tags': [fixture(Tag, {'name': 'GNOME'}),
                 fixture(Tag, {'name': 'KDE'}),
                 fixture(Tag, {'name': 'Window-Manager'})]
    }

    @with_fixtures('tags')
    def test_category_automatic_slug(self, fixtures):
        pass
