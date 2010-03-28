# -*- coding: utf-8 -*-
"""
    inyoka.news.subscriptions
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Subscription management for the Inyoka News application-

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.subscriptions import SubscriptionType
from inyoka.core.models import Tag
from inyoka.news.models import Article, Comment

class ArticleSubscriptionType(SubscriptionType):
    name = 'news.article.all'

    subject_type = None
    object_type = Article

    actions = ['news.new_article']
    mode = 'multiple'

    @classmethod
    def notify(cls, subscription, object, subject):
        print 'Notify %s about new article „%s“' % \
                (subscription.user.username, object.title)

#TODO: need support for multiple subjects per object
#class TagSubscriptionType(SubscriptionType):
#    name = 'news.article.by_tag'
#
#    subject_type = Tag
#    object_type = Article
#
#    actions = ['news.new_article', 'news.article.add_tag']
#    mode = 'multiple'
#
#    @classmethod
#    def notify(cls, subscription, object, subject):
#        print 'Notify %s about new article „%s“ with tag' % \
#                (subscription.user.username, object.title, subject.name)


class CommentSubscriptionType(SubscriptionType):
    name = 'news.comments'

    subject_type = Article
    object_type = Comment

    actions = ['news.new_comment']
    mode = 'sequent'

    @classmethod
    def get_subject(cls, object):
        return object.article

    @classmethod
    def notify(cls, subscription, object, subject):
        print 'Notify %s about new comment by %s on %s' % \
                (subscription.user.username, object.author.username,
                 subject.title)
