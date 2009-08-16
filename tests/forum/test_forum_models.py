#-*- coding: utf-8 -*-
"""
    forum/test_forum_models
    ~~~~~~~~~~~~~~~~~~~~~~~

    Some tests for our forum models. Untested models are Post, PostRevision,
    Attachment, ReadStatus


    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from __future__ import with_statement
from os import path
import unittest
from inyoka.conf import settings
from inyoka.forum.models import Forum, Topic, Privilege, WelcomeMessage, \
      Poll, PollOption, PollVote, Post
from inyoka.portal.user import User, PERMISSION_NAMES
from inyoka.forum.acl import PRIVILEGES_DETAILS, join_flags
from inyoka.utils.test import view, ViewTestCase, db, context
from inyoka.utils.parser import parse, RenderContext
from inyoka.utils.cache import cache
from datetime import datetime, timedelta


class TestForumModel(unittest.TestCase):
    """
    A class to test the Forum Model. At the moment we do not test the
    following methods :
    get_children_recursive
    invalidate_topic_cache <-- should be testable in test_forum_views
                               since there are the caches set
    """
    def setUp(self):
        """
        set up the test environment
        """
        self.welcome = WelcomeMessage("Mess", "text")
        self.category = Forum(name="c1", description="test category",
                           position=0, welcome_message=self.welcome)
        self.f1 = Forum(name="f1", position=1, parent=self.category)
        self.f2 = Forum(name="f2", position=2, parent=self.category)
        self.f3 = Forum(name='f3', position=1, parent=self.f1)
        self.user = User.query.register_user('test', 'ex@ex.com', 'pwd', False)

        permissions = 0
        for perm in PERMISSION_NAMES.keys():
            permissions |= perm
        self.user._permissions = permissions
        db.session.commit()

        bits = dict(PRIVILEGES_DETAILS).keys()
        bits = join_flags(*bits)
        for forum in Forum.query.all():
            p = Privilege(user=self.user, forum=forum, positive=bits)

        self.topic = Topic(title="t", slug=None, author=self.user)
        self.f1.topics.append(self.topic)
        db.session.commit()
        self.post = Post(author=self.user, text=u'Some cool Text!')
        self.topic.posts.append(self.post)
        db.session.commit()

    def tearDown(self):
        for forum in Forum.query.all():
            db.session.delete(forum)
        for p in Privilege.query.all():
            db.session.delete(p)
        db.session.delete(self.welcome)
        db.session.delete(self.user)
        db.session.delete(self.topic)
        db.session.delete(self.post)
        db.session.commit()

    def test_forum_cache(self):
        """Test if the forum query caches properly"""
        f = Forum.query.get(self.f1.id)
        self.assertEqual(self.f1, f)
        test_c1 = db.session.merge(cache.get('forum/forum/%d' % self.f1.id),
                                   dont_load=True)
        # we create a slug map first time we query for a slug
        f = Forum.query.get(self.f1.slug)
        self.assertEqual(cache.get('forum/slugs'), {
            self.f1.slug: self.f1.id,
            self.f2.slug: self.f2.id,
            self.f3.slug: self.f3.id,
            self.category.slug: self.category.id,
        })
        # cleanup caches
        cache.delete('forum/slugs')
        cache.delete('forum/forum/%d' % self.f1.id)

    def test_forum_mapper_extension(self):
        """test automatic slug generation, and cache deletion after update"""
        # automatic slug generation
        f = Forum(name='mapper extension test')
        self.assertEqual(f.slug, None)
        db.session.commit()
        self.assertEqual(f.slug, 'mapper-extension-test')

        # test that the caches are cleaned up after an update properly

        # fill the caches
        Forum.query.get(f.id)

        # change some bit...
        f.name = 'some other extension test name'
        db.session.commit()
        # ... and test that the caches are clean
        self.assertEqual(cache.get('forum/slugs'), None)
        self.assertEqual(cache.get('forum/forum/%d' % f.id), None)

        db.session.delete(f)
        db.session.commit()
        f = Forum.query.filter_by(slug='mapper-extension-text').first()
        self.assertEqual(f, None)

    def test_forum_properties(self):
        """
        test the properties of the Forum model
        """
        self.assertEqual(self.f1.parents, [self.category])
        self.assertEqual(self.category.children, [self.f1, self.f2])
        # test that the caches work properly
        c = cache.get('forum/children/%d' % self.category.id)
        self.assertEqual(c, [self.f1.id, self.f2.id])

    def test_forum_get_latest_topics(self):
        key = 'forum/latest_topics/%d' % self.f1.id
        self.assertEqual(self.f1.get_latest_topics(), [self.topic])
        self.assertEqual(self.f1.latest_topics, [self.topic])
        self.assertEqual(cache.get(key), [self.topic])
        self.assertEqual(self.category.get_latest_topics(), [])

        # assert that we don't cache non default topic counts
        cache.delete(key)
        self.category.get_latest_topics(settings.FORUM_TOPIC_CACHE + 10)
        self.assertEqual(cache.get(key), None)

    def test_forum_getters(self):
        """
        Test a few get functions.
        """
        #XXX: This is known to randomly fail because of a bug in sqlalchemy
        #     that prevents us from keeping the correct order for
        #     self-referential.
        #     See sqlalchemy-mailinglist (groups.google.com/sqlalchemy)
        #     topic: “Self references randomizes insert order”
        #     for more details

        self.assertEqual(self.category.children, [self.f1, self.f2])
        self.assertEqual(self.f1.children, [self.f3])
        self.assertEqual(list(self.category.all_children), [self.f1, self.f2, self.f3])
        self.assertEqual(list(self.f1.all_children), [self.f3])

        # real acl unittests can be found in forum/test_forum_acl.py
        # this is just to asure the function doesn't do any magic ;)
        self.assertEqual(self.category.get_children_filtered(self.user),
                         [self.f1, self.f2])
        self.assertEqual(self.category.get_children_filtered(context.anonymous),
                         [])

        # recursive children selection

        cq1 = list(Forum.get_children_recursive(Forum.query.all()))
        self.assertEqual(cq1, [(0, self.category), (1, self.f1), (1, self.f2)])
        # parent selection
        cq2 = list(Forum.get_children_recursive(Forum.query.all(), self.category.id))
        self.assertEqual(cq2, [(0, self.f1), (0, self.f2)])

    def test_forum_read(self):
        """
        test the mark read mechanism of the forum
        """
        self.assertEqual(self.category.get_read_status(self.user), False)
        self.category.mark_read(self.user)
        db.session.commit()
        self.assertEqual(self.category.get_read_status(self.user), True)

    def test_forum_welcome(self):
        """
        test the welcome message service
        """
        self.assertEqual(self.category.find_welcome(self.user), self.category)
        # the user does not accept the rules
        self.category.read_welcome(self.user, False)
        self.assertEqual(self.category.find_welcome(self.user), self.category)
        # but now he does...
        self.category.read_welcome(self.user)
        self.assertEqual(self.category.find_welcome(self.user), None)
        # and of course, there is no welcome message in c1, so don't show it
        self.assertEqual(self.f1.find_welcome(self.user), None)
        # anonymous users never ever can set the message to "read"
        self.assertEqual(self.category.find_welcome(context.anonymous), self.category)
        self.category.read_welcome(context.anonymous)
        self.assertEqual(self.category.find_welcome(context.anonymous), self.category)


class TestTopicModel(unittest.TestCase):
    """
    A class to test the Forum Model. At the moment we do not test the
    following methods :
    get_absolute_url - don't see why here
    get_pagination - don't see why here
    get_ubuntu_version - ""
    redindex - don't see the test
    """

    def setUp(self):
        """
        set up the test environment for the Topic Model
        """
        self.category = Forum(name='f1', description='test category',
                              position=0)
        db.session.commit()
        self.forum = Forum(name='f2', description='test forum',
                           position = 0, parent=self.category)
        self.user = User.query.register_user('u', 'ex@ex.com', 'pwd', False)

        permissions = 0
        for perm in PERMISSION_NAMES.keys():
            permissions |= perm
        self.user._permissions = permissions
        db.session.commit()

        bits = dict(PRIVILEGES_DETAILS).keys()
        bits = join_flags(*bits)
        for forum in Forum.query.all():
            p = Privilege(user=self.user, forum=forum, positive=bits)

        self.topic = Topic(title="t", slug=None, author=self.user)
        self.forum.topics.append(self.topic)
        db.session.commit()
        self.post = Post(author=self.user, text=u'Some cool Text!')
        self.topic.posts.append(self.post)
        db.session.commit()

    def tearDown(self):
        db.session.delete(self.forum)
        db.session.delete(self.category)
        for p in Privilege.query.all():
            db.session.delete(p)
        db.session.delete(self.topic)
        db.session.delete(self.user)
        db.session.commit()

    def test_topic_creation(self):
        """
        test if the Topic model is created automatically
        """
        t = Topic.query.filter_by(id = self.topic.id).first()
        self.assertEqual(t, self.topic)

    def test_topic_properties(self):
        """
        test the properties of the Topic model
        """
        self.assertNotEqual(self.topic.paginated, True)

    def test_topic_methods(self):
        """
        test the move and touch of the Topic
        """
        vc = self.topic.view_count
        f = Forum(name = "a", parent_id = 0)
        db.session.commit()

        self.topic.touch()
        self.topic.move(f)

        self.assertEqual(vc + 1 , self.topic.view_count)
        self.assertEqual(f.id, self.topic.forum_id)

        db.session.delete(f)
        db.session.commit()

    def test_topic_read(self):
        """
        test the mark read mechanism of the topic
        """
        self.assertEqual(self.topic.get_read_status(self.user), False)


class TestWelcomeMessageModel(unittest.TestCase):
    """
    A class to test the WelcomeMessage Model.
    """

    def setUp(self):
        """
        set up the test environment for the WelcomeMessage Model
        """
        self.message = WelcomeMessage(title = 'm1', text = 'Hello')
        db.session.commit()

    def tearDown(self):
        db.session.delete(self.message)
        db.session.commit()

    def test_welcomeMessage_creation(self):
        """
        test the automatic creation of WelcomeMessage
        """
        m = WelcomeMessage.query.filter_by(id = self.message.id).first()
        self.assertEqual(m, self.message)

    def test_welcomeMessage_render(self):
        """
        test the text rendering of WelcomeMessage
        """
        # TODO : this could be much more complete
        context = RenderContext(None, simplified = True)
        text = parse(self.message.text).render(context, 'html')
        self.assertEqual(text, self.message.render_text())


class TestPrivilegeModel(unittest.TestCase):
    """
    A class to test the Privilege Model.
    """
    def test_privilege_creation(self):
        """
        test the creation of a Privilege
        """
        forum = Forum(name = "f1", parent_id = 0)
        user = User.query.register_user('test', 'ex@ex.com', 'pwd', False)
        db.session.commit()

        permissions = 0
        for perm in PERMISSION_NAMES.keys():
            permissions |= perm
        user._permissions = permissions
        db.session.commit()

        bits = dict(PRIVILEGES_DETAILS).keys()
        bits = join_flags(*bits)
        self.assertRaises(ValueError, Privilege, forum = forum)

        #TODO :  we should test every other different combination with
        # negative groups etc. too
        privilege = Privilege(forum, user)
        db.session.commit()

        p = Privilege.query.filter_by(id = privilege.id).first()
        self.assertEquals(p.id, privilege.id)

        db.session.delete(forum)
        db.session.delete(privilege)
        db.session.delete(user)
        db.session.commit()


class TestPollModel(unittest.TestCase):
    """
    A class to test the Poll Model. At the moment we do not test the
    following methods :
    participated - no current request exists
    can_vote - ""
    """

    def setUp(self):
        """
        set up the test environment for the Topic Model
        """
        self.forum = Forum(name = "f1", description= "test forum",
                            position = 0, parent_id = 0)
        self.user = User.query.register_user('u', 'ex@ex.com', 'pwd', False)

        permissions = 0
        for perm in PERMISSION_NAMES.keys():
            permissions |= perm
        self.user._permissions = permissions
        db.session.commit()

        bits = dict(PRIVILEGES_DETAILS).keys()
        bits = join_flags(*bits)
        for forum in Forum.query.all():
            p = Privilege(user=self.user, forum=forum, positive=bits)

        self.topic = Topic(title = "t", forum = self.forum, slug = None,
                            post_count = 0, author_id = self.user.id)

        db.session.commit()

        now = datetime.utcnow()

        self.po1 = PollOption(name = 'po1')
        self.pv = PollVote(voter_id = self.user.id)
        self.poll = Poll(topic = self.topic, question = "What?",
                          multiple_votes = False, start_time = now,
                          end_time = now + timedelta(days = 2),
                          options = [self.po1], votings = [self.pv])
        db.session.commit()

    def tearDown(self):
        db.session.delete(self.forum)
        db.session.delete(self.user)
        db.session.delete(self.topic)
        db.session.delete(self.poll)
        db.session.delete(self.po1)
        db.session.delete(self.pv)
        db.session.commit()

    def test_poll_creation(self):
        """
        test the creation of the Poll model
        """
        p = Poll.query.filter_by(id = self.poll.id).first()
        self.assertEquals(p, self.poll)

    def test_poll_properties(self):
        """
        test the properties of the Poll
        """
        self.assertEquals(self.poll.ended, False)
        now = datetime.utcnow()
        p = Poll(topic = self.topic, question = "What now?",multiple_votes = False,
                  start_time = now, end_time = now - timedelta(days = 1))
        db.session.commit()
        self.assertEquals(p.ended, True)
        db.session.delete(p)

        self.assertEquals(self.poll.has_participated(self.user), True)
        self.po1.votes = 2
        self.assertEquals(self.poll.votes, 2)


class TestPollOptionModel(unittest.TestCase):
    """
    A class to test the PollOption Model.
    """

    def setUp(self):
        """
        set up the test environment for the PollOption Model
        """
        self.forum = Forum(name = "f1", description= "test forum",
                            position = 0, parent_id = 0)
        self.user = User.query.register_user('u', 'ex@ex.com', 'pwd', False)

        permissions = 0
        for perm in PERMISSION_NAMES.keys():
            permissions |= perm
        self.user._permissions = permissions
        db.session.commit()

        bits = dict(PRIVILEGES_DETAILS).keys()
        bits = join_flags(*bits)
        for forum in Forum.query.all():
            p = Privilege(user=self.user, forum=forum, positive=bits)

        self.topic = Topic(title = "t", forum = self.forum, slug = None,
                            post_count = 0, author_id = self.user.id)

        db.session.commit()

        now = datetime.utcnow()

        # create the poll to test
        self.poll = Poll(topic = self.topic, question = "What?",
                          multiple_votes = False, start_time = now,
                          end_time = now + timedelta(days = 2))
        self.po1 = PollOption(name = "po1", poll = self.poll)
        self.po2 = PollOption(name = "po2", poll = self.poll)
        db.session.commit()

    def tearDown(self):
        db.session.delete(self.forum)
        db.session.delete(self.user)
        db.session.delete(self.topic)
        db.session.delete(self.poll)
        db.session.delete(self.po1)
        db.session.delete(self.po2)
        db.session.commit()

    def test_pollOption_creation(self):
        """
        test the creation of the PollOption model
        """
        p = PollOption.query.filter_by(id = self.po1.id).first()
        self.assertEquals(p, self.po1)

    def test_pollOption_properties(self):
        """
        test the properties of the PollOption
        """
        self.po1.votes = 1
        self.po2.votes = 2
        self.assertEquals(self.po1.percentage, 1. / 3 * 100)
