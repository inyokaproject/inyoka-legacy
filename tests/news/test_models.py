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
from inyoka.news.models import Article, Tag, Comment



class TestNewsModels(DatabaseTestCase):

    fixtures = [{
        User: [
            {'&bob': {'username': u'Bob', 'email': u'bob@noone.com'}},
            {'&peter': {'username': u'Peter', 'email': u'peter@noo.com'}}
        ]}, {
        Tag: [
            {'&ubuntu': {'name': u'Ubuntu'}},
            {'&ubuntuusers': {'name': u'Ubuntuusers'}}
        ]}, {
        Article: [
            {'&rocks_article': {
                'title': u'My Ubuntu rocks!!',
                'intro': u'Well, it just rocks!!',
                'text': u'And because you\'re so tschaka baam, you\'re using Ubuntu!!',
                'public': 'Y',
                'tags': ['*ubuntu'],
                'author': '*bob'
            }}
        ]}, {
        Comment: [{'text': u'Bah, cool article!', 'author': '*bob', 'article': '*rocks_article'},
                  {'text': u'This article sucks!', 'author': '*bob', 'article': '*rocks_article'}]
    }]

    def test_article_attributes(self):
        article = self.data['Article'][0]
        eq_(article.slug, 'my-ubuntu-rocks')

    def test_comment_counter(self):
        article = self.data['Article'][0]
        eq_(article.comment_count, 2)

    def test_article_automatic_updated_pub_date(self):
        article = self.data['Article'][0]
        eq_(article.was_updated, False)
        article.updated = article.pub_date + datetime.timedelta(days=2)
        db.session.commit()
        eq_(article.was_updated, True)
