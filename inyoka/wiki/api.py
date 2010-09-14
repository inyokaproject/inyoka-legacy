# -*- coding: utf-8 -*-
"""
    inyoka.wiki.api
    ~~~~~~~~~~~~~~~

    API description for the wiki application.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IResourceManager
from inyoka.core.config import TextConfigField
from inyoka.wiki.models import Page, Revision, Text, Attachment


class WikiResourceManager(IResourceManager):

    #: Name to the wiki index page (the one a user accessing the wiki's ’/’
    #: is redirected to)
    wiki_index_name = TextConfigField('wiki.index.name', default=u'Main Page')

    models = [Page, Revision, Text, Attachment]
