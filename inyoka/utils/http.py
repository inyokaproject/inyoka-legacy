# -*- coding: utf-8 -*-
"""
    inyoka.utils.http
    ~~~~~~~~~~~~~~~~~

    Various http utilities

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug.exceptions import NotFound
from jinja2.utils import escape

from inyoka.core.api import templated
from inyoka.portal.controllers import context_modifier


@templated('portal/404.html', modifier=context_modifier)
def notfound(request, urls):
    rule_iterator = sorted(urls.map.iter_rules(),
                           key=lambda x: (x.subdomain, x.rule))
    rules = [escape(repr(rule)) for rule in rule_iterator]
    return {'url_list': rules}
