# -*- coding: utf-8 -*-
"""
    inyoka.news.subscriptions
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Subscription management for the Inyoka News application.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from operator import attrgetter
from inyoka.core.subscriptions import SubscriptionType, SubscriptionAction
from inyoka.core.models import Tag
from inyoka.news.models import Article, Comment


class ArticleSubscriptionType(SubscriptionType):
    name = 'news.article.all'

    subject_type = None
    object_type = Article

    actions = ['news.article.new']
    mode = 'multiple'


class TagSubscriptionType():# SubscriptionType):
    #XXX articles have only one tag atm.
    name = 'news.article.by_tag'

    subject_type = Tag
    object_type = Article

    actions = ['news.article.new']#, 'news.article.add_tag']
    mode = 'multiple'

    get_subjects = staticmethod(attrgetter('tags'))


class CommentSubscriptionType(SubscriptionType):
    name = 'news.comments.by_entry'

    subject_type = Article
    object_type = Comment

    actions = ['news.comment.new']
    mode = 'sequent'

    get_subject = staticmethod(attrgetter('article'))


class NewArticleSubscriptionAction(SubscriptionAction):
    name = 'news.article.new'

    @classmethod
    def notify(cls, user, object, subjects):
        print 'Notify %s about new article „%s“' % \
                (user.username, object.title)


class NewCommentSubscriptionAction(SubscriptionAction):
    name = 'news.comment.new'

    @classmethod
    def notify(cls, user, object, subjects):
        print 'Notify %s about new comment by %s on %s' % \
                (user.username, object.author.username,
                 object.article.title)
