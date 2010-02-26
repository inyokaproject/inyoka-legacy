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
    ChoiceLoader, FileSystemBytecodeCache, MemcachedBytecodeCache
from inyoka import INYOKA_REVISION, l10n, i18n
from inyoka.core.context import ctx
from inyoka.core.http import Response
from inyoka.core.routing import href
from inyoka.core.cache import cache as inyoka_cache
from inyoka.core.exceptions import NotFound
from inyoka.core.database import db


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


def render_template(template_name, context, stream=False):
    """Renders a template.  If `stream` is ``True`` the return value will be
    a Jinja template stream and not an unicode object.
    This is useful for pages with lazy generated content or huge output
    where you don't want the users to wait until the calculation ended.
    Use streaming only in those situations because it's usually slower than
    bunch processing.
    """
    tmpl = jinja_env.get_template(template_name)
    populate_context_defaults(context)
    return tmpl.render(context)


def templated(template_name, modifier=None, stream=False):
    """
    This function can be used as a decorator to use a function's return value
    as template context if it's not a valid Response object.
    The first decorator argument must be the template to use::

        @templated('mytemplate.html')
        def index(request):
            return {
                'articles': Article.query.all()
            }

    :exc:`~inyoka.core.database.NoResultFound` exceptions are catched
    and raised again as :exc:`~inyoka.core.exceptions.NotFound`.

    :param template_name: The name of the template to render.
    :param modifier: A callback to modify the template context on-the-fly.
    :param stream: Use Jinja template streaming, see :func:`render_template`
                   for more details.
    """
    def decorator(func):
        @functools.wraps(func)
        def templated_wrapper(request, *args, **kwargs):
            try:
                ret = func(request, *args, **kwargs)
                if ret is None:
                    ret = {}
            except db.NoResultFound:
                raise NotFound()

            # if we got no dictionary as response type we try to force
            # to return a proper Response object instead of any further process
            if not isinstance(ret, dict):
                return Response.force_type(ret)

            # apply the context modifier
            if modifier is not None:
                modifier(request, ret)

            data = render_template(template_name, ret, stream=stream)
            response = Response(data)
            if ctx.cfg['debug']:
                TEMPLATE_CONTEXT.clear()
                TEMPLATE_CONTEXT.update(ret)
            return response
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
            timedelta=l10n.timedeltaformat,
            monthformat=l10n.format_month
        )
        self.install_gettext_translations(
            i18n.get_translations()
        )


jinja_env = InyokaEnvironment()
