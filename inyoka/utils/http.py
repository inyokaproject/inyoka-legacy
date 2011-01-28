# -*- coding: utf-8 -*-
"""
    inyoka.utils.http
    ~~~~~~~~~~~~~~~~~

    Various http utilities

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from markupsafe import escape

from inyoka.core.api import render_template, Response
from inyoka.portal.controllers import context_modifier


def notfound(request, urls):
    rule_iterator = sorted(urls.map.iter_rules(),
                           key=lambda x: (x.subdomain, x.rule))
    rules = [escape(repr(rule)) for rule in rule_iterator]
    return Response(render_template('portal/404.html', modifier=context_modifier,
        context={'url_list': rules}), status=404)
