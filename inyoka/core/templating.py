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
import functools
from jinja2 import Environment, FileSystemLoader, StrictUndefined, \
    ChoiceLoader, BytecodeCache, FileSystemBytecodeCache, \
    MemcachedBytecodeCache
from inyoka import INYOKA_REVISION
from inyoka import l10n, i18n
from inyoka.core.context import ctx
from inyoka.core.http import Response
from inyoka.core.routing import href


TEMPLATE_CONTEXT = {}


def populate_context_defaults(context):
    """Fill in context defaults."""
    try:
        context.update({
            'request': ctx.current_request
        })
    except AttributeError:
        # Don't raise an error if we don't have a request as it's
        # used get render_template which can get called by the message
        # broker to deliver notifications etc…
        pass


def render_template(template_name, context):
    """Render a template."""
    tmpl = jinja_env.get_template(template_name)
    populate_context_defaults(context)
    return tmpl.render(context)


def templated(template_name):
    """
    Decorator for views. The decorated view must return a dictionary which is
    default_mimetype = 'text/html'
    then used as context for the given template. Returns a Response object.
    """
    def decorator(func):
        @functools.wraps(func)
        def templated_wrapper(*args, **kwargs):
            ret = func(*args, **kwargs)
            if ret is None:
                ret = {}
            if isinstance(ret, dict):
                data = render_template(template_name, ret)
                response = Response(data)
                if ctx.cfg['debug']:
                    TEMPLATE_CONTEXT.clear()
                    TEMPLATE_CONTEXT.update(ret)
                return response
            return Response.force_type(ret)
        return templated_wrapper
    return decorator


class InyokaEnvironment(Environment):
    """
    Beefed up version of the jinja environment but without security features
    to improve the performance of the lookups.
    """

    def __init__(self):
        template_paths = [os.path.join(os.path.dirname(__file__), os.pardir,
                                       'templates')]
        if ctx.cfg['templates.path']:
            template_paths.insert(0,  ctx.cfg['templates.path'])

        loaders = []
        for path in template_paths:
            loaders.append(FileSystemLoader(
                searchpath=path
            ))

        loader = ChoiceLoader(loaders)
        cache_obj = None
        if ctx.cfg['templates.use_cache']:
            if ctx.cfg['templates.use_memcached_cache']:
                cache_obj = MemcachedBytecodeCache(
                    client=inyoka_cache,
                    timeout=ctx.cfg['caching.timeout']
                )
            elif ctx.cfg['templates.use_filesystem_cache']:
                cache_obj = FileSystemBytecodeCache(
                    directory=ctx.cfg['caching.filesystem_cache_path'],
                )

        Environment.__init__(self,
            loader=loader,
            extensions=['jinja2.ext.i18n', 'jinja2.ext.do'],
            auto_reload=ctx.cfg['templates.auto_reload'],
            undefined=StrictUndefined,
            cache_size=-1,
            bytecode_cache=cache_obj
        )
        self.globals.update(
            INYOKA_REVISION=INYOKA_REVISION,
            href=href,
        )
        self.filters.update(
            jsonencode=simplejson.dumps,
            datetimeformat=l10n.format_datetime,
            dateformat=l10n.format_date,
        )
        self.install_gettext_translations(
            i18n.get_translations()
        )


jinja_env = InyokaEnvironment()
