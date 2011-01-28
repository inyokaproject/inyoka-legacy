# -*- coding: utf-8 -*-
"""
    inyoka.utils.feeds
    ~~~~~~~~~~~~~~~~~~

    Atom feed utilities.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from functools import wraps
from werkzeug.contrib.atom import AtomFeed
from inyoka.core.cache import cache
from inyoka.core.http import Response


def atom_feed(cache_key=None, endpoint=None, cache_timeout=600):
    def decorator(original):
        @wraps(original)
        def func(*args, **kwargs):
            if cache_key is not None:
                key = cache_key % kwargs
                content = cache.get(key)
                if content is not None:
                    mimetype = 'application/atom+xml; charset=utf-8'
                    return Response(content, mimetype=mimetype)

            feed = original(*args, **kwargs)
            if not isinstance(feed, AtomFeed):
                # ret is not a feed object so return it
                return feed

            response = feed.get_response()

            if cache_key is not None:
                cache.set(key, response.data, cache_timeout)
            return response

        # set the endpoint if not already done – this can save the additional
        # @view decorator.
        func.endpoint = endpoint or getattr(original, 'endpoint', original.__name__)
        return func

    return decorator
