# -*- coding: utf-8 -*-
"""
    Test news models
    ~~~~~~~~~~~~~~~~

    Unittests for our news models.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import datetime
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


def get_comments():
    art = Article.query.get(1)
    c1 = Comment(text=u'Bah, cool article!', author=get_user_callback(),
                 article=art)
    c2 = Comment(text=u'This article suck!', author=get_user_callback(),
                 article=art)
    return [c1, c2]


class TestNewsModels(TestSuite):

    fixtures = {
        'categories': [
            fixture(Category, {'name': 'Ubuntu'}),
            fixture(Category, {'name': 'Ubuntuusers'})
        ],
        'articles': [fixture(Article, get_article_data)],
        'comments': get_comments
    }

    @with_fixtures('categories')
    def test_category_automatic_slug(self, fixtures):
        category = fixtures['categories'][0]
        eq_(category.slug, 'ubuntu')

    @with_fixtures('categories', 'articles')
    def test_article_attributes(self, fixtures):
        article = fixtures['articles'][0]
        eq_(article.slug, 'my-ubuntu-rocks')

    @with_fixtures('categories', 'articles', 'comments')
    def test_comment_counter(self, fixtures):
        article = fixtures['articles'][0]
        eq_(article.comment_count, 2)

    @with_fixtures('categories')
    def test_article_automatic_updated_pub_date(self, fixtures):
        category = fixtures['categories'][0]
        article = Article(title=u'foo', intro=u'bar', text=u'baz', public=True,
                          category=category, author=get_user_callback())
        db.session.commit()
        eq_(article.was_updated, False)
        article.updated = article.pub_date + datetime.timedelta(days=2)
        db.session.commit()
        eq_(article.was_updated, True)
        # cleanup
        db.session.delete(article)
        db.session.commit()
