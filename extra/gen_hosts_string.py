# -*- coding: utf-8 -*-
"""
    gen_hosts_string
    ~~~~~~~~~~~~~~~~

    This script generates the string that must be added to a /etc/hosts file
    to finally setup inyoka development.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from urllib2 import splitport
from inyoka.core.api import ctx

print u' '.join((sub +'.' if sub else sub) + splitport(ctx.dispatcher.get_url_adapter().server_name)[0] for sub in sorted(set(rule.subdomain for rule in ctx.dispatcher.url_map.iter_rules())))
