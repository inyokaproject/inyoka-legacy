# -*- coding: utf-8 -*-
"""
    tests.core.test_subscriptions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for the subscription system.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import unittest
from operator import attrgetter
from inyoka import setup_components
from inyoka.core.api import db
from inyoka.core.auth.models import User
from inyoka.core.subscriptions import SubscriptionType
from inyoka.core.subscriptions.models import Subscription
from inyoka.core.test import *

# to keep it better understandable classes etc are named like in a blog


class Category(db.Model):
    __tablename__ = '_test_subscription_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))

class Entry(db.Model):
    __tablename__ = '_test_subscription_entry'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.ForeignKey(Category.id))
    category = db.relation(Category)
    title = db.Column(db.String(30))

class Comment(db.Model):
    __tablename__ = '_test_subscription_comment'
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.ForeignKey(Entry.id), nullable=False)
    entry = db.relation(Entry)


class NotifyTrackerMixin(object):
    tracker = []
    @classmethod
    def notify(cls, s, object, subject=None):
        NotifyTrackerMixin.tracker. \
            append((cls.name, s.user, object, subject))


class CategorySubscriptionType(SubscriptionType, NotifyTrackerMixin):
    name = '__test_category'
    subject_type = Category
    object_type = Entry
    mode = 'multiple'

    get_subject = attrgetter('category')

class BlogSubscriptionType(SubscriptionType, NotifyTrackerMixin):
    name = '__test_blog'
    is_singleton = True
    object_type = Entry
    mode = 'multiple'

class CommentsSubscriptionType(SubscriptionType, NotifyTrackerMixin):
    name = '__test_comments'
    subject_type = Entry
    object_type = Comment
    mode = 'sequent'

    get_subject = attrgetter('entry')



class TestSubscriptions(TestSuite):

    fixtures = {
        'eins': fixture(User, username='eins', email='eins@example.com'),
        'zwei': fixture(User, username='zwei', email='zwei@example.com'),
        'drei': fixture(User, username='drei', email='drei@example.com'),
        'vier': fixture(User, username='vier', email='vier@example.com')
    }

    def setUp(self):
        setup_components([])

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

    @future
    def test_subscriptiontype(self):
        eq_(SubscriptionType.by_name('__test_comments'), CommentsSubscriptionType)
        eq_(SubscriptionType.by_object_type(Comment), [CommentsSubscriptionType])
        eq_(SubscriptionType.by_subject_type()[Category], [CategorySubscriptionType])

    @future
    @with_fixtures('eins', 'zwei', 'drei', 'vier')
    def test_subscribing(self, users):
        cat1 = Category(name='cat1')
        cat2 = Category(name='cat2')
        db.session.add_all([cat1, cat2])
        db.session.commit()


        # mode=multiple:
        Subscription.subscribe(users['eins'], '__test_category', cat1)
        Subscription.subscribe(users['zwei'], '__test_blog')

        NotifyTrackerMixin.tracker = []
        e = [Entry(category=cat1), Entry(category=cat2), Entry(category=cat1),
             Entry(category=cat1), Entry(category=cat1), Entry(category=cat1)]
        db.session.add_all(e)

        Subscription.new(e[0])
        Subscription.new(e[1])
        self._check_multiple_state(users['eins'], '__test_category', cat1.id,
                              set((e[0].id,)), 1)
        self._check_multiple_state(users['zwei'], '__test_blog', None,
                              set((e[0].id, e[1].id)), 2)

        Subscription.new(e[2])
        Subscription.new(e[3])
        self._check_multiple_state(users['eins'], '__test_category', cat1.id,
                              set((e[0].id, e[2].id, e[3].id)), 3)
        self._check_multiple_state(users['zwei'], '__test_blog', None,
                              set((e[0].id, e[1].id, e[2].id, e[3].id)), 4)

        Subscription.accessed(users['zwei'], e[2])
        Subscription.accessed(users['zwei'], e[1])
        self._check_multiple_state(users['zwei'], '__test_blog', None,
                              set((e[0].id, e[3].id)), 2)

        eq_(sorted(NotifyTrackerMixin.tracker), sorted([
            ('__test_blog', users['zwei'], e[0], None),
            ('__test_category', users['eins'], e[0], cat1),
            ('__test_blog', users['zwei'], e[1], None),
            ('__test_category', users['eins'], e[2], cat1),
            ('__test_blog', users['zwei'], e[2], None),
            ('__test_category', users['eins'], e[3], cat1),
            ('__test_blog', users['zwei'], e[3], None),
        ]))


        # mode=sequent:
        Subscription.subscribe(users['drei'], '__test_comments', e[0])
        Subscription.subscribe(users['drei'], '__test_comments', e[1])
        Subscription.subscribe(users['vier'], '__test_comments', e[0])

        e1, e2 = e[:2]
        NotifyTrackerMixin.tracker = []
        c = [Comment(entry=e1), Comment(entry=e2), Comment(entry=e1),
                    Comment(entry=e1), Comment(entry=e1), Comment(entry=e2)]
        db.session.add_all(c)
        db.session.commit()

        Subscription.new(c[0]) # e1
        Subscription.new(c[1]) # e2

        self._check_sequent_state(users['drei'], '__test_comments', e1.id,
                            c[0].id, 1)
        self._check_sequent_state(users['drei'], '__test_comments', e2.id,
                            c[1].id, 1)
        self._check_sequent_state(users['vier'], '__test_comments', e1.id,
                            c[0].id, 1)

        Subscription.accessed(users['drei'], c[0])
        self._check_sequent_state(users['drei'], '__test_comments', e1.id,
                             None, 0)

        Subscription.new(c[2]) # e1
        self._check_sequent_state(users['drei'], '__test_comments', e1.id,
                             c[2].id, 1)

        Subscription.new(c[3]) # e1
        self._check_sequent_state(users['drei'], '__test_comments', e1.id,
                             c[2].id, 2)
        self._check_sequent_state(users['vier'], '__test_comments', e1.id,
                             c[0].id, 3)

        Subscription.accessed(users['vier'], c[3])
        self._check_sequent_state(users['vier'], '__test_comments', e1.id,
                             None, 0)

        Subscription.new(c[4]) # e1
        Subscription.new(c[5]) # e2
        self._check_sequent_state(users['drei'], '__test_comments', e1.id,
                             c[2].id, 3)
        self._check_sequent_state(users['drei'], '__test_comments', e2.id,
                             c[1].id, 2)
        self._check_sequent_state(users['vier'], '__test_comments', e1.id,
                             c[4].id, 1)

        eq_(sorted(NotifyTrackerMixin.tracker), sorted([
            ('__test_comments', users['drei'], c[0], e1),
            ('__test_comments', users['vier'], c[0], e1),
            ('__test_comments', users['drei'], c[1], e2),
            # here drei accesses entry 1
            ('__test_comments', users['drei'], c[2], e1),
            # here vier accesses entry 1
            ('__test_comments', users['vier'], c[4], e1),
        ]))
