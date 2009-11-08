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
from inyoka.core.context import get_request
from inyoka.core.http import Response
from inyoka.core.config import config
from inyoka.core.routing import href
from inyoka.utils.urls import url_encode, url_quote

# Used for debugging
TEMPLATE_CONTEXT = {}

def populate_context_defaults(context):
    """Fill in context defaults."""
    if get_request():
        context.update(
            CURRENT_URL=get_request().build_absolute_url(),
            REQUEST=get_request()
        )


def render_template(template_name, context):
    """Render a template.  You might want to set `req` to `None`."""
    tmpl = jinja_env.get_template(template_name)
    populate_context_defaults(context)
    return tmpl.render(context)


def templated(template_name):
    """
    Decorator for views. The decorated view must return a dictionary which is
    default_mimetype = 'text/html'
    then used as context for the given template. Returns a Response object.
    """
    def templated_(f):
        def templated__(*args, **kwargs):
            ret = f(*args, **kwargs)
            if ret is None:
                ret = {}
            if isinstance(ret, dict):
                data = render_template(template_name, ret)
                if config['debug'] == True:
                    TEMPLATE_CONTEXT.clear()
                    TEMPLATE_CONTEXT.update(ret)
                return Response(data)
            return Response.force_type(ret)
        return templated__
    return templated_

def url_filter(model_instance, action=None):
    """
    Call `get_absolute_url` on a model instance.
    """
    # filters don't take **kwargs?
    kwargs = {}
    if action is not None: kwargs['action'] = action
    return model_instance.get_absolute_url(**kwargs)


class InyokaEnvironment(Environment):
    """
    Beefed up version of the jinja environment but without security features
    to improve the performance of the lookups.
    """

    def __init__(self):
        template_paths = [os.path.join(os.path.dirname(__file__), os.pardir,
                                       'templates')]
        if config['template_path']:
            template_paths.insert(0,  config['template_path'])

        loader = FileSystemLoader(os.path.join(os.path.dirname(__file__),
                                               os.pardir, 'templates'))
        #TODO: link `auto_reload` to a config setting
        Environment.__init__(self, loader=loader,
                             extensions=['jinja2.ext.i18n', 'jinja2.ext.do'],
                             auto_reload=True,
                             cache_size=-1)
        self.globals.update(
            INYOKA_REVISION=INYOKA_REVISION,
            href=href,
        )
        self.filters.update(
            jsonencode=simplejson.dumps,
            url=url_filter,
        )

        self.install_null_translations()

jinja_env = InyokaEnvironment()
