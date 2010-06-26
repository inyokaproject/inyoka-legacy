# -*- coding: utf-8 -*-
"""
    inyoka.news
    ~~~~~~~~~~~

    The integrated news portal application for Inyoka.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.news.admin import NewsAdminProvider
from inyoka.news.models import NewsSchemaController, ArticlesContentProvider, \
    LatestCommentsContentProvider
from inyoka.news.controllers import NewsController
from inyoka.news.subscriptions import ArticleSubscriptionType, TagSubscriptionType, \
    CommentSubscriptionType, NewArticleSubscriptionAction, NewCommentSubscriptionAction
