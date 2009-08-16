#-*- coding: utf-8 -*-
"""
    forum/test_forum_views
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module tests the Forum views
"""
from inyoka.utils.test import view, ViewTestCase, db, context
from inyoka.forum.models import Forum

class TestIndexView(ViewTestCase):
    """
    Test the index view.
    """

    component = 'forum'

    def setUp(self):
        self.category = Forum(name='test_index_view_category')
        db.session.commit()
        self.forum = Forum(name='test_index_view_forum', parent_id=self.category.id)
        db.session.commit()
        # set privileges for the `admin` user
        context.add_forum(self.category)
        context.add_forum(self.forum)
        db.session.commit()
        self.login({'username': 'admin', 'password': 'admin'})

    def tearDown(self):
        context.delete_forum(self.forum)
        context.delete_forum(self.category)
        self.logout()

    def test_index_is_index(self):
        """
        test the is_index key of the Index view
        """
        tctx = self.get_context('/')
        self.assertEqual(tctx['is_index'], True)
        tctx = self.get_context('/category/%s/' % self.category.slug)
        self.assertEqual(tctx['is_index'], False)
        tctx = self.get_context('/category/%s/' % self.forum.slug)
        self.assertEqual(self.response.app.status_code, 404)

    def test_index_categories(self):
        """
        test the categories key of the Index view
        """
        tctx = self.get_context('/category/%s/' % self.category.slug)
        self.assertEqual(tctx['categories'], [self.category])

    def test_index_hidden_categories(self):
        """
        test the hidden_categories key of the Index view
        """
        tctx = self.get_context('/category/%s/' % self.category.slug)
        self.assertEqual(tctx['hidden_categories'], [])


class TestForumView(ViewTestCase):
    """
    Test the forum view.
    """

    component = 'forum'

    def setUp(self):
        self.category = Forum(name="test_forum_view_category")
        db.session.commit()
        self.forum = Forum(name="test_forum_view_forum", parent_id=self.category.id)
        db.session.commit()
        context.add_forum(self.category)
        context.add_forum(self.forum)
        self.login({'username': 'admin', 'password': 'admin'})

    def tearDown(self):
        context.delete_forum(self.forum)
        context.delete_forum(self.category)
        self.logout()

    def test_forum_forum(self):
        """
        test the forum key of the Forum view
        """
        tctx = self.get_context('/forum/%s/' % self.category.slug)
        self.assertEqual(self.response.app.status_code, 404)
        tctx = self.get_context('/forum/%s/' % self.forum.slug)
        self.assertEqual(tctx['forum'], self.forum)
