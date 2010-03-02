# -*- coding: utf-8 -*-
"""
    Test news models
    ~~~~~~~~~~~~~~~~

    Unittests for our news models.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core.auth.models import User
from inyoka.news.models import Article, Category, Comment


def get_user_callback():
    return User.query.get_anonymous()


def get_article_data():
    cat = Category.query.filter_by(slug=u'ubuntu').one()
    return {
        'title': u'My Ubuntu rocks!!',
        'intro': u'Well, it just rocks!!',
        'text': u'And because you\'re so tschaka baam, you\'re using Ubuntu!!',
        'public': True, 'category': cat, 'author': get_user_callback()
    }


class TestEntryModel(TestSuite):

    fixtures = {
        'categories': [
            fixture(Category, {'name': 'Ubuntu'}),
            fixture(Category, {'name': 'Ubuntuusers'})
        ],
        'articles': [fixture(Article, get_article_data)],
        'comments': [
            fixture(Comment, {'text': u'Bah, cool article!',
                'author_id': 2, 'article_id': 1}),
            fixture(Comment, {'text': u'This article suck!',
                'author_id': 1, 'article_id': 1})
        ]
    }

    @with_fixtures('categories')
    def test_category_automatic_slug(self, fixtures):
        category = fixtures['categories'][0]
        eq_(category.slug, 'ubuntu')

    @with_fixtures('categories', 'articles')
    def test_article_attributes(self, fixtures):
        article = fixtures['articles'][0]
        eq_(article.slug, 'my-ubuntu-rocks')
