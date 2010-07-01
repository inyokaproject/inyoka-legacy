# -*- coding: utf-8 -*-
"""
    inyoka.utils.urls
    ~~~~~~~~~~~~~~~~~

    Various utilities for url handling, checking and modifying.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import urlparse
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


def get_host_port_mapping(value):
    url_scheme = urlparse.urlsplit(value)[0]
    pieces = value.split(':', 1)
    host = pieces[0]
    if len(pieces) == 2 and pieces[1].isdigit():
        port = int(pieces[1])
    elif url_scheme == 'https':
        port = 443
    else:
        port = 80

    return host, port, scheme
