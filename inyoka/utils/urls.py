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


def make_full_domain(subdomain=None, path=None):
    """Return the full domain based on `subdomain`

    >>> from inyoka.core.api import ctx
    >>> from inyoka.utils.urls import make_full_domain
    >>> ctx.cfg['base_domain_name'] = 'example.com'
    >>> make_full_domain()
    u'http://example.com/'
    >>> make_full_domain(u'www')
    u'http://www.example.com/'
    >>> make_full_domain(u'www', 'faz')
    u'http://www.example.com/faz/'
    >>> del ctx.cfg['base_domain_name']

    """
    subdomain, path = (subdomain or u''), (path or u'')
    adapter = ctx.dispatcher.url_adapter
    path = path.strip('/')

    return u'%s://%s%s%s/%s' % (
        adapter.url_scheme,
        subdomain and subdomain + '.' or '',
        adapter.server_name,
        adapter.script_name[:-1],
        path + '/' if path else ''
    )


def get_host_port_mapping(value):
    url = urlparse.urlsplit(value)
    pieces = url.netloc.split(':')
    host = pieces[0]
    if len(pieces) == 2 and pieces[1].isdigit():
        port = int(pieces[1])
    elif url.scheme == 'https':
        port = 443
    else:
        port = 80

    return host, port, url.scheme


def get_base_url_for_controller(controller=None):
    """Get the url root representing the `controller`.

    Examples::

        >>> ctx.cfg['base_domain_name'] = 'inyoka.local:5000'
        >>> ctx.cfg['routing.urls.news'] = 'news:/'
        >>> get_base_url_for_controller(u'news')
        u'http://news.inyoka.local:5000/'

        # Support for empty controller name
        >>> get_base_url_for_controller(u'')
        u'http://inyoka.local:5000/'
        >>> ctx.cfg['routing.urls.news'] = ':/_news'
        >>> get_base_url_for_controller(u'news')
        u'http://inyoka.local:5000/_news/'

    """
    subdomain, path = None, None
    if not isinstance(controller, basestring):
        controller = controller.name

    if controller:
        parts = ctx.cfg['routing.urls.' + controller].split(':', 1)
        subdomain, path = parts

    return make_full_domain(subdomain or u'', path)
