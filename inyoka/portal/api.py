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


class ILatestContentProvider(Interface):
    """A :cls:`ILatestContentProvider` implementation provides a interface
    that pushes the recent created content on the portal index page.

    The application itself should only provide the query and the neccessary
    properties, but no internal caching because this interface does that
    in a more sophisticated way so that all components are refreshed together.

    """

    #: The app or content name this content is from.  Take 'forum', 'wiki',
    #: 'news' for example.  To provide application-information use a underscore
    #: for seperation.
    name = None

    #: The cache timeout in seconds.  This will be applied to the cache backend.
    cache_timeout = 120

    #: The cache key to search in the cache.
    cache_key = None

    def get_query(self):
        """Return a query that returns the proper latest content.  Note that
        we must work with a query object here but not with another iterable!
        """

    @staticmethod
    def get_cached_content(max_per_impl=4):
        contents = []
        for provider in ctx.get_implementations(ILatestContentProvider, True):
            objects = None

            if provider.cache_key is not None:
                objects = cache.get(provider.cache_key)
            if objects is None:
                objects = provider.get_query().limit(max_per_impl).all()

            if provider.cache_key is not None:
                cache.set(provider.cache_key, objects, provider.cache_timeout)

            merge = db.session.merge
            objects = [(provider.name, merge(obj, load=False)) for obj in objects]
            contents.extend(objects)
        return contents
