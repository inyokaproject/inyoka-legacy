# -*- coding: utf-8 -*-
"""
    inyoka.testing.components
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Components for usage within tests.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sys, os
from operator import attrgetter
from inyoka.core.api import Response, IController, Rule, view, \
    render_template, config
from inyoka.core.auth import get_auth_system
from inyoka.core.subscriptions import SubscriptionType
from werkzeug import redirect


class TestingController(IController):
    name = 'testing'

    url_rules = [
    ]


#XXX: that's just plain ugly, we need to think of something better here...
if config['debug']:
    sys.path.insert(0, os.getcwd())
    from tests.core.test_subscriptions import Category, Entry, Comment

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
