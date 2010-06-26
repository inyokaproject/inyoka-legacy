# -*- coding: utf-8 -*-
"""
    inyoka.utils.urls
    ~~~~~~~~~~~~~~~~~

    Various utilities for url handling, checking and modifying.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.context import ctx
from werkzeug import url_encode, url_decode, url_quote, \
     url_quote_plus, url_fix


def make_full_domain(subdomain=''):
    """Return the full domain based on :attr:`subdomain`

    >>> from inyoka.core.api import ctx
    >>> from inyoka.utils.urls import make_full_domain
    >>> ctx.cfg['base_domain_name'] = 'example.com'
    >>> make_full_domain()
    u'http://example.com/'
    >>> make_full_domain('www')
    u'http://www.example.com/'
    >>> del ctx.cfg['base_domain_name']

    """
    adapter = ctx.dispatcher.url_adapter

    return unicode('%s://%s%s%s/' % (
        adapter.url_scheme,
        subdomain and subdomain + '.' or '',
        adapter.server_name,
        adapter.script_name[:-1]
    ))
