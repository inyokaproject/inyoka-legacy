# -*- coding: utf-8 -*-
"""
    inyoka.utils.urls
    ~~~~~~~~~~~~~~~~~

    Description goes here...

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import url_encode, url_decode, url_quote, url_quote_plus, \
    url_fix
from inyoka.core.config import config
from inyoka.core.context import current_application


def make_full_domain(subdomain=''):
    """Return the full domain based on :attr:`subdomain`

    >>> from inyoka.core.api import config
    >>> config['base_domain_name'] = 'example.com'
    >>> make_full_domain()
    u'example.com'
    >>> make_full_domain('www')
    u'www.example.com'
    >>> del config['base_domain_name']

    """
    if not subdomain:
        return config['base_domain_name']
    return u'%s.%s' % (subdomain, config['base_domain_name'])


def url_for(endpoint, **args):
    """Get the URL to an endpoint.  The keyword arguments provided are used
    as URL values.  Unknown URL values are used as keyword argument.
    Additionally there are some special keyword arguments:

    `_anchor`
        This string is used as URL anchor.

    `_external`
        If set to `True` the URL will be generated with the full server name
        and `http://` prefix.
    """
    anchor = args.pop('_anchor', None)
    external = args.pop('_external', False)
    rv = current_application.url_adapter.build(endpoint, args,
        force_external=external)
    if anchor is not None:
        rv += '#' + url_quote(anchor)
    return rv
