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
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from inyoka import INYOKA_REVISION
from inyoka.core.context import current_request
from inyoka.core.http import Response
from inyoka.core.config import config
from inyoka.core.routing import href


TEMPLATE_CONTEXT = {}


def populate_context_defaults(context):
    """Fill in context defaults."""
    try:
        context.update(
            CURRENT_URL=current_request.build_absolute_url(),
            REQUEST=current_request
        )
    except RuntimeError:
        # Don't raise an error if we don't have a request as it's
        # used get render_template which can get called by the message
        # broker to deliver notifications etc…
        pass


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
    def _proxy(f):
        def _func(*args, **kwargs):
            ret = f(*args, **kwargs)
            if ret is None:
                ret = {}
            if isinstance(ret, dict):
                data = render_template(template_name, ret)
                response = Response(data)
                if config['debug']:
                    TEMPLATE_CONTEXT.clear()
                    TEMPLATE_CONTEXT.update(ret)
                return response
            return Response.force_type(ret)
        return _func
    return _proxy


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
                             auto_reload=True, undefined=StrictUndefined,
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
