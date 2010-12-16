# -*- coding: utf-8 -*-
"""
    inyoka.portal.api
    ~~~~~~~~~~~~~~~~~

    Interface descriptions for our portal app.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka import Interface
from inyoka.core.api import ctx, cache, db
from inyoka.core.resource import IResourceManager
from inyoka.portal.search import PortalSearchIndex
from inyoka.utils.decorators import abstract


class IPortalResourceManager(IResourceManager):

    #: register portal search index
    search_indexes = [PortalSearchIndex()]


class ITaggableContentProvider(Interface):
    """Interface to find all providers that provide taggable contents"""

    #: The type of the content provider
    type = None

    #: The name of the content.  This is shown in the public view.
    name = None

    @abstract
    def get_taggable_content(self, tag):
        """Return a query that returns all contents for that provider.

        Do never return a list but a query object!

        :param tag: The tag object to specify the tag the content must
                    relate to.
        """
