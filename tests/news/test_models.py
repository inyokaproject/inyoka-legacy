# -*- coding: utf-8 -*-
"""
    Test paste models

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core.auth.models import User
from inyoka.news.models import Article, Category, Comment


def get_user_callback():
    return User.query.get('anonymous')


class TestEntryModel(TestSuite):

    fixtures = {
        'categories': [fixture(Category, {'name': 'Category1'})]
    }

    @with_fixtures('categories')
    def test_category_automatic_slug(self, fixtures):
        category = fixtures['categories'][0]
        eq_(category.slug, 'category1')
