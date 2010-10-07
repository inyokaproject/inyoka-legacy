# -*- coding: utf-8 -*-
"""
    inyoka.news.api
    ~~~~~~~~~~~~~~~

    API description for the news application.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IResourceManager
from inyoka.news.models import Article, Comment, article_tag
from inyoka.news.search import NewsSearchProvider


class NewsResourceManager(IResourceManager):
    models = [Article, Comment, article_tag]
    search_providers = [NewsSearchProvider()]
