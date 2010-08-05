# -*- coding: utf-8 -*-
"""
    inyoka.wiki.api
    ~~~~~~~~~~~~~~~

    API description for the wiki application.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IResource
from inyoka.wiki.models import WikiLatestContentProvider, Page, Revision, \
    Text, Attachment
from inyoka.wiki.controllers import WikiController

class WikiResource(IResource):
    models = [Page, Revision, Text, Attachment]
