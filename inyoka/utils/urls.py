# -*- coding: utf-8 -*-
"""
    inyoka.utils.urls
    ~~~~~~~~~~~~~~~~~

    Description goes here...

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GPL, see LICENSE for more details.
"""
from werkzeug import url_encode, url_decode, url_quote, url_quote_plus, \
    url_fix


def make_full_domain(subdomain=''):
    from inyoka.core.config import config
    if not subdomain:
        return config['base_domain_name']
    return '%s.%s' % (subdomain, config['base_domain_name'])
