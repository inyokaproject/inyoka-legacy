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

NOTFOUND_DEBUG_TEMPLATE = """
    <p>We tried these urls:</p>
    %s
"""

def notfound_with_debug(urls):
    tmp = []
    for r in sorted(urls.map.iter_rules(), key=lambda x: (x.subdomain,x.rule)):
        tmp.append(escape(repr(r)))
    return NotFound(NOTFOUND_DEBUG_TEMPLATE % '<br/>'.join(tmp))

@templated('portal/404.html', modifier=context_modifier)
def notfound(request):
    return {}
