# -*- coding: utf-8 -*-
"""
    tests.core.test_subscriptions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for the subscription system.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import unittest
from operator import attrgetter
from inyoka.core.api import db, ctx
from inyoka.core.auth.models import User
from inyoka.core.subscriptions import SubscriptionType
from inyoka.core.subscriptions.models import Subscription
from inyoka.core.test import *

# to keep it better understandable classes etc are named like in a blog


class Category(db.Model):
    __tablename__ = '_test_subscription_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))


class Wrapper(db.Model):
    __tablename__ = '_test_subscription_wrapper'
    id = db.Column(db.Integer, primary_key=True)


class Entry(db.Model):
    __tablename__ = '_test_subscription_entry'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.ForeignKey(Category.id))
    category = db.relationship(Category)
    title = db.Column(db.String(30))


class Comment(db.Model):
    __tablename__ = '_test_subscription_comment'
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.ForeignKey(Entry.id), nullable=False)
    entry = db.relationship(Entry)


class Other(db.Model):
    __tablename__ = '_test_subscription_other'
    id = db.Column(db.Integer, primary_key=True)
    wrapper_id = db.Column(db.ForeignKey(Wrapper.id))
    wrapper = db.relationship(Wrapper)


class SubscriptionTestSchemaController(db.ISchemaController):
    models = [Category, Entry, Comment, Wrapper, Other]


class NotifyTrackerMixin(object):
    tracker = []
    @classmethod
    def notify(cls, s, object, subject=None):
        NotifyTrackerMixin.tracker.append((cls.name, s.user, object, subject))


class CategorySubscriptionType(SubscriptionType, NotifyTrackerMixin):
    name = '__test_category'
    subject_type = Category
    object_type = Entry
    mode = 'multiple'
    actions = ['__test_new_entry']

    get_subject = attrgetter('category')

class BlogSubscriptionType(SubscriptionType, NotifyTrackerMixin):
    name = '__test_blog'
    subject_type = None
    object_type = Entry
    mode = 'multiple'
    actions = ['__test_new_entry']

class BadImplementedType(SubscriptionType, NotifyTrackerMixin):
    name = '__test_something'
    subject_type = Wrapper
    object_type = Other
    mode = 'multiple'
    actions = ['__test_new_other']

class CommentsSubscriptionType(SubscriptionType, NotifyTrackerMixin):
    name = '__test_comments'
    subject_type = Entry
    object_type = Comment
    mode = 'sequent'
    actions = ['__test_new_comment']

    get_subject = attrgetter('entry')


class TestSubscriptions(TestSuite):

    fixtures = {
        'one': fixture(User, username='one', email='one@example.com'),
        'two': fixture(User, username='two', email='two@example.com'),
        'three': fixture(User, username='three', email='three@example.com'),
        'four': fixture(User, username='four', email='four@example.com'),
        'categories': [fixture(Category, name='cat1'), fixture(Category, name='cat2')],
        'entries': [fixture(Entry, category_id=1), fixture(Entry, category_id=2),
                    fixture(Entry, category_id=1), fixture(Entry, category_id=1)]
    }

    def _check_sequent_state(self, user, type_name, subject_id, first_unread, count):
        """
        Check if values of `first_unread_object_id` and `count` attributes of
        Subscription with given parameters are equal to the given values.
        """
        s = Subscription.query.filter_by(user=user, type_name=type_name,
                                         subject_id=subject_id).one()
        eq_(s.first_unread_object_id, first_unread)
        eq_(s.count, count)

    def _check_multiple_state(self, user, type_name, subject_id, unread_object_ids, count):
        """
        Check if values of `unread_object_ids` and `count` attributes of
        Subscription with given parameters are equal to the given values.
        """
        s = Subscription.query.filter_by(user=user, type_name=type_name,
                                         subject_id=subject_id).one()
        eq_(s.unread_object_ids, unread_object_ids)
        eq_(s.count, count)

    def test_subscriptiontype(self):
        eq_(SubscriptionType.by_name('__test_comments'), CommentsSubscriptionType)
        eq_(SubscriptionType.by_object_type(Comment), [CommentsSubscriptionType])
        eq_(SubscriptionType.by_subject_type(Category), [CategorySubscriptionType])

    @with_fixtures('one', 'two', 'categories', 'entries')
    def test_multiple_subscriptions(self, fixtures):
        cat1, cat2 = fixtures['categories']
        one, two = fixtures['one'], fixtures['two']
        entries = fixtures['entries']

        Subscription.subscribe(one, '__test_category', cat1)
        Subscription.subscribe(two, '__test_blog')

        Subscription.new(entries[0], '__test_new_entry')
        Subscription.new(entries[1], '__test_new_entry')
        self._check_multiple_state(one, '__test_category', cat1.id,
                              set((entries[0].id,)), 1)
        self._check_multiple_state(two, '__test_blog', None,
                              set((entries[0].id, entries[1].id)), 2)

        Subscription.new(entries[2], '__test_new_entry')
        Subscription.new(entries[3], '__test_new_entry')
        self._check_multiple_state(one, '__test_category', cat1.id,
                              set((entries[0].id, entries[2].id, entries[3].id)), 3)
        self._check_multiple_state(two, '__test_blog', None,
                              set((entries[0].id, entries[1].id,
                                   entries[2].id, entries[3].id)), 4)

        # check for not well implemented subscription types
        w1 = Wrapper()
        db.session.commit()
        assert_raises(NotImplementedError,
            lambda: Subscription.new(Other(wrapper=w1), '__test_new_other'))

        Subscription.accessed(two, entries[2])
        Subscription.accessed(two, entries[1])
        self._check_multiple_state(two, '__test_blog', None,
                              set((entries[0].id, entries[3].id)), 2)

        eq_(sorted(NotifyTrackerMixin.tracker), sorted([
            ('__test_blog', two, entries[0], None),
            ('__test_category', one, entries[0], cat1),
            ('__test_blog', two, entries[1], None),
            ('__test_category', one, entries[2], cat1),
            ('__test_blog', two, entries[2], None),
            ('__test_category', one, entries[3], cat1),
            ('__test_blog', two, entries[3], None),
        ]))

    @with_fixtures('three', 'four', 'categories', 'entries')
    def test_multiple_subscriptions(self, fixtures):
        cat1, cat2 = fixtures['categories']
        three, four = fixtures['three'], fixtures['four']

        e1, e2 = fixtures['entries'][:2]

        Subscription.subscribe(three, '__test_comments', e1)
        Subscription.subscribe(three, '__test_comments', e2)
        Subscription.subscribe(four, '__test_comments', e1)

        self._check_sequent_state(three, '__test_comments', e1.id,
                                  None, 0)
        self._check_sequent_state(three, '__test_comments', e2.id,
                                  None, 0)
        self._check_sequent_state(four, '__test_comments', e1.id,
                                  None, 0)

        NotifyTrackerMixin.tracker = []
        comments = [Comment(entry=e1), Comment(entry=e2), Comment(entry=e1),
                    Comment(entry=e1), Comment(entry=e1), Comment(entry=e2)]
        db.session.commit()

        Subscription.new(comments[0], '__test_new_comment') # e1
        Subscription.new(comments[1], '__test_new_comment') # e2

        self._check_sequent_state(three, '__test_comments', e1.id,
                                  comments[0].id, 1)
        self._check_sequent_state(three, '__test_comments', e2.id,
                                  comments[1].id, 1)
        self._check_sequent_state(four, '__test_comments', e1.id,
                                  comments[0].id, 1)

        Subscription.accessed(three, comments[0])
        self._check_sequent_state(three, '__test_comments', e1.id,
                                  None, 0)

        Subscription.new(comments[2], '__test_new_comment') # e1
        self._check_sequent_state(three, '__test_comments', e1.id,
                             comments[2].id, 1)

        Subscription.new(comments[3], '__test_new_comment') # e1
        self._check_sequent_state(three, '__test_comments', e1.id,
                             comments[2].id, 2)
        self._check_sequent_state(four, '__test_comments', e1.id,
                             comments[0].id, 3)

        Subscription.accessed(four, comments[3])
        self._check_sequent_state(four, '__test_comments', e1.id,
                             None, 0)

        Subscription.new(comments[4], '__test_new_comment') # e1
        Subscription.new(comments[5], '__test_new_comment') # e2
        self._check_sequent_state(three, '__test_comments', e1.id,
                             comments[2].id, 3)
        self._check_sequent_state(three, '__test_comments', e2.id,
                             comments[1].id, 2)
        self._check_sequent_state(four, '__test_comments', e1.id,
                             comments[4].id, 1)

        eq_(sorted(NotifyTrackerMixin.tracker), sorted([
            ('__test_comments', three, comments[0], e1),
            ('__test_comments', four, comments[0], e1),
            ('__test_comments', three, comments[1], e2),
            # here three accesses entry 1
            ('__test_comments', three, comments[2], e1),
            # here four accesses entry 1
            ('__test_comments', four, comments[4], e1),
        ]))
