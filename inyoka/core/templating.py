# -*- coding: utf-8 -*-
"""
    inyoka.core.templating
    ~~~~~~~~~~~~~~~~~~~~~~

    Description goes here...

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import simplejson
from jinja2 import Environment, FileSystemLoader
from inyoka import INYOKA_REVISION
from inyoka.core.context import current_request
from inyoka.core.http import Response
from inyoka.utils.urls import url_encode, url_quote


def populate_context_defaults(context):
    """Fill in context defaults."""
    if current_request:
        context.update(
            CURRENT_URL=current_request.build_absolute_uri(),
        )


def render_template(template_name, context):
    """Render a template.  You might want to set `req` to `None`."""
    tmpl = jinja_env.get_template(template_name)
    populate_context_defaults(context)
    return tmpl.render(context)

def render_to_response(template_name, context, mimetype='text/html'):
    content = render_template(template_name, context)
    return Response(content, mimetype=mimetype)


def urlencode_filter(value):
    """URL encode a string or dict."""
    if isinstance(value, dict):
        return url_encode(value)
    return url_quote(value)


def templated(template_name):
    '''
    Decorator for views. The decorated view must return a dictionary which is
    default_mimetype = 'text/html'
    then used as context for the given template. Returns a Response object.
    '''
    def decorator(f):
        def proxy(*args, **kwargs):
            ret = f(*args, **kwargs)
            if isinstance(ret, dict):
                return render_to_response(template_name, context=ret)
            return Response.force_type(ret)
        return proxy
    return decorator


class InyokaEnvironment(Environment):
    """
    Beefed up version of the jinja environment but without security features
    to improve the performance of the lookups.
    """

    def __init__(self):
        loader = FileSystemLoader(os.path.join(os.path.dirname(__file__),
                                               os.pardir, 'templates'))
        #TODO: link `auto_reload` to a config setting
        Environment.__init__(self, loader=loader,
                             extensions=['jinja2.ext.i18n', 'jinja2.ext.do'],
                             auto_reload=True,
                             cache_size=-1)
        self.globals.update(
            INYOKA_REVISION=INYOKA_REVISION,
            REQUEST=current_request,
        )
        self.filters.update(
            jsonencode=simplejson.dumps
        )

        self.install_null_translations()

jinja_env = InyokaEnvironment()
