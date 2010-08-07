# -*- coding: utf-8 -*-
"""
    inyoka.news.api
    ~~~~~~~~~~~~~~~

    API description for the news application.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IResourceManager
from inyoka.news.admin import NewsAdminProvider
from inyoka.news.controllers import NewsController
from inyoka.news.subscriptions import ArticleSubscriptionType, TagSubscriptionType, \
    CommentSubscriptionType, NewArticleSubscriptionAction, NewCommentSubscriptionAction
from inyoka.news.models import Article, Comment, article_tag


class NewsResourceManager(IResourceManager):
    models = [Article, Comment, article_tag]
