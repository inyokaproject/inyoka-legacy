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
from inyoka.core.subscriptions import SubscriptionType, SubscriptionAction
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


_entry_tag = db.Table('_test_subscription_entry_tag', db.metadata,
    db.Column('entry_id', db.Integer, db.ForeignKey(Entry.id)),
    db.Column('tag_id', db.Integer,
              db.ForeignKey('_test_subscription_tag.id')),
)

class Tag(db.Model):
    __tablename__ = '_test_subscription_tag'
    id = db.Column(db.Integer, primary_key=True)
    entries = db.relationship(Entry, secondary=_entry_tag, backref='tags',
                              lazy='joined')


class Other(db.Model):
    __tablename__ = '_test_subscription_other'
    id = db.Column(db.Integer, primary_key=True)
    wrapper_id = db.Column(db.ForeignKey(Wrapper.id))
    wrapper = db.relationship(Wrapper)


class SubscriptionTestSchemaController(db.ISchemaController):
    models = [Category, Entry, Comment, Wrapper,
              Other, Tag, _entry_tag]


class NotifyTrackerMixin(object):
    tracker = []
    epoch = 0
    @classmethod
    def notify(cls, user, object, subjects):
        NotifyTrackerMixin.tracker.append((NotifyTrackerMixin.epoch, cls.name,
            user, object, subjects))


class NewEntrySubscriptionAction(NotifyTrackerMixin, SubscriptionAction):
    name = u'__test_new_entry'

class NewCommentSubscriptionAction(NotifyTrackerMixin, SubscriptionAction):
    name = u'__test_new_comment'

class NewOtherSubscriptionAction(SubscriptionAction):
    name = u'__test_new_other'

    @classmethod
    def notify(cls, user, subscriptions):
        raise RuntimeError('This should not have been called')

class CategorySubscriptionType(SubscriptionType):
    name = u'__test_category'
    subject_type = Category
    object_type = Entry
    mode = u'multiple'
    actions = [u'__test_new_entry']

    get_subject = attrgetter('category')

class BlogSubscriptionType(SubscriptionType):
    name = u'__test_blog'
    subject_type = None
    object_type = Entry
    mode = u'multiple'
    actions = [u'__test_new_entry']

class BadImplementedType(SubscriptionType):
    name = u'__test_something'
    subject_type = Wrapper
    object_type = Other
    mode = u'multiple'
    actions = [u'__test_new_other']

class CommentsSubscriptionType(SubscriptionType):
    name = u'__test_comments'
    subject_type = Entry
    object_type = Comment
    mode = u'sequent'
    actions = [u'__test_new_comment']

    get_subject = attrgetter('entry')

class TagSubscriptionType(SubscriptionType):
    name = u'__test_tag'
    subject_type = Tag
    object_type = Entry
    mode = u'multiple'
    actions = [u'__test_new_entry']

    get_subjects = attrgetter('tags')


class TestSubscriptions(DatabaseTestCase):

    fixtures = [
        {'User': [{'username': 'one', 'email': 'one@example.com'},
                  {'username': 'two', 'email': 'two@example.com'},
                  {'username': 'three', 'email': 'three@example.com'},
                  {'username': 'four', 'email': 'four@example.com'}]},
        {Category: [{'id': '&c1', 'name': 'cat1'},
                    {'id': '&c2', 'name': 'cat2'}]},
        {Entry:   [{'&e1': {'category_id': '*c1'}},
                   {'&e2': {'category_id': '*c2'}},
                   {'&e3': {'category_id': '*c1'}},
                   {'&e4': {'category_id': '*c1'}}]},
        {Tag: [{'entries': ['*e1']}, {'entries': ['*e1', '*e2', '*e4']},
               {'entries': ['*e4']}]},
        {Comment: [{'entry': '*e1'}, {'entry': '*e2'}, {'entry': '*e1'},
                   {'entry': '*e1'}, {'entry': '*e1'}, {'entry': '*e2'}]}
    ]

    custom_cleanup_factories = [
        lambda: Subscription.query.all()
    ]

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
        eq_(SubscriptionType.by_name(u'__test_comments'), CommentsSubscriptionType)
        eq_(SubscriptionType.by_object_type(Comment), [CommentsSubscriptionType])
        eq_(SubscriptionType.by_subject_type(Category), [CategorySubscriptionType])
        eq_(sorted(SubscriptionType.by_action(NewEntrySubscriptionAction)),
            sorted([CategorySubscriptionType, BlogSubscriptionType, TagSubscriptionType]))
        eq_(SubscriptionType.by_action(u'__test_new_comment'), [CommentsSubscriptionType])

    def test_subscription(self):
        one = self.data['User'][0]
        cat1, cat2 = self.data['Category']
        eq_(Subscription.subscribe(one, u'__test_category', cat1), True)
        eq_(Subscription.subscribe(one, u'__test_category', cat1), False)
        eq_(Subscription.subscribe(one, u'__test_blog'), True)
        eq_(Subscription.subscribe(one, u'__test_blog'), False)

        s = Subscription.query.filter_by(user_id=one.id,
                                         type_name=u'__test_category',
                                         subject_id=cat1.id).one()
        eq_(s.type, CategorySubscriptionType)
        eq_(s.subject, cat1)
        s = Subscription.query.filter_by(user_id=one.id,
                                         type_name=u'__test_blog').one()
        eq_(s.type, BlogSubscriptionType)
        eq_(s.subject, None)

    def test_multiple_subscriptions(self):
        """
        Test (with multiple mode) whether the subscription count and the unread
        information is accurate and whether notifications are sent correctly.
        """
        cat1, cat2 = self.data['Category']
        one, two, three, four = self.data['User']
        entries = self.data['Entry']
        NotifyTrackerMixin.tracker = []

        #: ensure this does not fail but passes silently
        Subscription.accessed(one, object=entries[0])

        Subscription.subscribe(one, u'__test_category', cat1)
        Subscription.subscribe(two, u'__test_blog')

        NotifyTrackerMixin.epoch = 1
        Subscription.new(entries[0], u'__test_new_entry')
        Subscription.new(entries[1], u'__test_new_entry')
        self._check_multiple_state(one, u'__test_category', cat1.id,
                              set((entries[0].id,)), 1)
        self._check_multiple_state(two, u'__test_blog', None,
                              set((entries[0].id, entries[1].id)), 2)

        NotifyTrackerMixin.epoch = 2
        Subscription.new(entries[2], u'__test_new_entry')
        Subscription.new(entries[3], u'__test_new_entry')
        self._check_multiple_state(one, u'__test_category', cat1.id,
                              set((entries[0].id, entries[2].id, entries[3].id)), 3)
        self._check_multiple_state(two, u'__test_blog', None,
                              set((entries[0].id, entries[1].id,
                                   entries[2].id, entries[3].id)), 4)

        Subscription.accessed(two, object=entries[2])
        Subscription.accessed(two, object=entries[1])
        self._check_multiple_state(two, u'__test_blog', None,
                              set((entries[0].id, entries[3].id)), 2)

        Subscription.accessed(one, subject=cat1)
        Subscription.accessed(one, subject=cat1) # must work also if not unread
        self._check_multiple_state(one, u'__test_category', cat1.id,
                              set(), 0)

        eq_(sorted(NotifyTrackerMixin.tracker), sorted([
            (1, u'__test_new_entry', one, entries[0], {'__test_category': [cat1]}),
            (1, u'__test_new_entry', two, entries[0], {'__test_blog': [None]}),
            (1, u'__test_new_entry', two, entries[1], {'__test_blog': [None]}),
            (2, u'__test_new_entry', one, entries[2], {'__test_category': [cat1]}),
            (2, u'__test_new_entry', one, entries[3], {'__test_category': [cat1]}),
            (2, u'__test_new_entry', two, entries[2], {'__test_blog': [None]}),
            (2, u'__test_new_entry', two, entries[3], {'__test_blog': [None]}),
        ]))

    def test_multiple_multiple_subscriptions(self):
        """
        Test (with multiple mode and a SubscriptionType where there is more
        then one subject per object) whether the subscription count and the
        unread information is accurate and whether notifications are sent
        correctly.
        """
        entries = self.data['Entry']
        cat1, cat2 = self.data['Category']
        one, two, three, four = self.data['User']
        t1, t2, t3 = self.data['Tag']

        NotifyTrackerMixin.tracker = []

        Subscription.subscribe(three, u'__test_tag', t1)
        Subscription.subscribe(three, u'__test_tag', t2)
        Subscription.subscribe(three, u'__test_category', cat2)
        Subscription.subscribe(four, u'__test_tag', t3)

        self._check_multiple_state(three, u'__test_tag', t1.id,
                                   set(), 0)
        self._check_multiple_state(three, u'__test_tag', t2.id,
                                   set(), 0)
        self._check_multiple_state(four, u'__test_tag', t3.id,
                                   set(), 0)

        NotifyTrackerMixin.epoch = 1
        Subscription.new(entries[0], u'__test_new_entry')
        NotifyTrackerMixin.epoch = 2
        Subscription.new(entries[2], u'__test_new_entry')
        self._check_multiple_state(three, u'__test_tag', t1.id,
                                   set((entries[0].id,)), 1)
        self._check_multiple_state(three, u'__test_tag', t2.id,
                                   set((entries[0].id,)), 1)

        NotifyTrackerMixin.epoch = 3
        Subscription.new(entries[1], u'__test_new_entry')
        self._check_multiple_state(three, u'__test_tag', t2.id,
                                   set((entries[0].id, entries[1].id)), 2)

        self._check_multiple_state(three, u'__test_category', cat2.id,
                                   set((entries[1].id,)), 1)
        Subscription.accessed(three, object=entries[1])
        Subscription.accessed(three, object=entries[1])
        self._check_multiple_state(three, u'__test_category', cat2.id,
                                   set(), 0)

        NotifyTrackerMixin.epoch = 4
        Subscription.new(entries[3], u'__test_new_entry')
        self._check_multiple_state(three, u'__test_tag', t1.id,
                                   set((entries[0].id,)), 1)
        self._check_multiple_state(three, u'__test_tag', t2.id,
                                   set((entries[0].id, entries[3].id)), 2)
        self._check_multiple_state(four, u'__test_tag', t3.id,
                                   set((entries[3].id,)), 1)

        eq_(sorted(NotifyTrackerMixin.tracker), sorted([
            (1, u'__test_new_entry', three, entries[0], {'__test_tag': [t1, t2]}),
            (3, u'__test_new_entry', three, entries[1], {'__test_tag': [t2],
                                                '__test_category': [cat2]}),
            (4, u'__test_new_entry', three, entries[3], {'__test_tag': [t2]}),
            (4, u'__test_new_entry', four, entries[3], {'__test_tag': [t3]}),
        ]))

    def test_sequent_subscriptions(self):
        """
        Test (with sequent mode) whether the subscription count and the unread
        information is accurate and whether notifications are sent correctly.
        """
        cat1, cat2 = self.data['Category']
        one, two, three, four = self.data['User']
        e1, e2 = self.data['Entry'][:2]
        comments = self.data['Comment']

        NotifyTrackerMixin.tracker = []

        Subscription.subscribe(three, u'__test_comments', e1)
        Subscription.subscribe(three, u'__test_comments', e2)
        Subscription.subscribe(four, u'__test_comments', e1)

        self._check_sequent_state(three, u'__test_comments', e1.id,
                                  None, 0)
        self._check_sequent_state(three, u'__test_comments', e2.id,
                                  None, 0)
        self._check_sequent_state(four, u'__test_comments', e1.id,
                                  None, 0)

        NotifyTrackerMixin.epoch = 1
        Subscription.new(comments[0], u'__test_new_comment') # e1
        Subscription.new(comments[1], u'__test_new_comment') # e2

        self._check_sequent_state(three, u'__test_comments', e1.id,
                                  comments[0].id, 1)
        self._check_sequent_state(three, u'__test_comments', e2.id,
                                  comments[1].id, 1)
        self._check_sequent_state(four, u'__test_comments', e1.id,
                                  comments[0].id, 1)

        Subscription.accessed(three, subject=e1)
        self._check_sequent_state(three, u'__test_comments', e1.id,
                                  None, 0)

        NotifyTrackerMixin.epoch = 2
        Subscription.new(comments[2], u'__test_new_comment') # e1
        self._check_sequent_state(three, u'__test_comments', e1.id,
                             comments[2].id, 1)

        NotifyTrackerMixin.epoch = 3
        Subscription.new(comments[3], u'__test_new_comment') # e1
        self._check_sequent_state(three, u'__test_comments', e1.id,
                             comments[2].id, 2)
        self._check_sequent_state(four, u'__test_comments', e1.id,
                             comments[0].id, 3)

        Subscription.accessed(four, object=comments[3])
        self._check_sequent_state(four, u'__test_comments', e1.id,
                             None, 0)

        NotifyTrackerMixin.epoch = 4
        Subscription.new(comments[4], u'__test_new_comment') # e1
        Subscription.new(comments[5], u'__test_new_comment') # e2
        self._check_sequent_state(three, u'__test_comments', e1.id,
                             comments[2].id, 3)
        self._check_sequent_state(three, u'__test_comments', e2.id,
                             comments[1].id, 2)
        self._check_sequent_state(four, u'__test_comments', e1.id,
                             comments[4].id, 1)

        eq_(sorted(NotifyTrackerMixin.tracker), sorted([
            (1, u'__test_new_comment', three, comments[0], {'__test_comments': [e1]}),
            (1, u'__test_new_comment', four, comments[0], {'__test_comments': [e1]}),
            (1, u'__test_new_comment', three, comments[1], {'__test_comments': [e2]}),
            # here three accesses entry 1
            (2, u'__test_new_comment', three, comments[2], {'__test_comments': [e1]}),
            # here four accesses entry 1
            (4, u'__test_new_comment', four, comments[4], {'__test_comments': [e1]}),
        ]))

    @refresh_database
    def check_bad_implemented_type(self):
        """check for not well implemented subscription types"""
        w1 = Wrapper()
        db.session.commit()
        assert_raises(NotImplementedError,
            lambda: Subscription.new(Other(wrapper=w1), u'__test_new_other'))
