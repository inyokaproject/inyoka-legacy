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
            }},
            {'&hidden_article': {
                'title': u'My hidden article',
                'intro': u'Well, this sucks...',
                'text': u'This is hidden because not really published?',
                'public': 'N',
                'author': '*bob'
            }},
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
        comment = Comment(author=self.data['User'][0], text=u'some comment')
        article.comments.append(comment)
        db.session.commit()
        eq_(article.comment_count, 3)
        # check that decremention of the counter works
        article.comments.remove(comment)
        db.session.delete(comment)
        db.session.commit()
        eq_(article.comment_count, 2)

    def test_article_automatic_updated_pub_date(self):
        article = self.data['Article'][0]
        eq_(article.was_updated, False)
        article.updated = article.pub_date + datetime.timedelta(days=2)
        db.session.commit()
        eq_(article.was_updated, True)

    def test_article_view_counter(self):
        article = self.data['Article'][0]
        self.assertEqual(article.view_count, 0)
        article.touch()
        self.assertEqual(article.view_count, 1)
        article.touch()
        self.assertEqual(article.view_count, 2)

    def test_article_visibility(self):
        visible, invisible = self.data['Article']
        self.assertFalse(visible.hidden)
        self.assertTrue(invisible.hidden)
        self.assertEqual(Article.query.published().all(), [visible])
        self.assertEqual(Article.query.hidden().all(), [invisible])
        invisible.public = True
        db.session.commit()
        self.assertEqual(Article.query.published().all(), [visible, invisible])
        invisible.pub_date = datetime.datetime.utcnow() + datetime.timedelta(days=2)
        db.session.commit()
        self.assertTrue(invisible.hidden)
        self.assertEqual(Article.query.published().all(), [visible])

