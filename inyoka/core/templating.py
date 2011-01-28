# -*- coding: utf-8 -*-
"""
    inyoka.core.templating
    ~~~~~~~~~~~~~~~~~~~~~~

    Description goes here...

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import sys
import json
import functools
from threading import Lock
from jinja2 import Environment, FileSystemLoader, StrictUndefined, \
    ChoiceLoader, FileSystemBytecodeCache, MemcachedBytecodeCache, \
    PrefixLoader
from inyoka import INYOKA_REVISION, l10n, i18n
from inyoka.context import ctx
from inyoka.signals import signals
from inyoka.core.http import Response
from inyoka.core.routing import href, IServiceProvider
from inyoka.core.resource import IResourceManager
from inyoka.core.cache import cache as inyoka_cache
from inyoka.core.config import TextConfigField, BooleanConfigField


#! This signal is raised if a template is rendered.  Use it to catch context variables
#! and such stuff.
template_rendered = signals.signal('template-rendered')

#: The default templates path
_default_templates_path = os.path.join(os.environ['INYOKA_MODULE'], 'templates')

#: Custom template path which is searched before the default path
templates_path = TextConfigField('templates.path', default=_default_templates_path)

#: Auto reload template files if they changed
templates_auto_reload = BooleanConfigField('templates.auto_reload', default=True)

#: Use either ’memory’, ’filesystem’, or ’memcached’ bytecode caches
templates_use_cache = BooleanConfigField('templates.use_cache', default=False)

#: Use memcached for bytecode caching
templates_use_memcached_cache = BooleanConfigField('templates.use_memcached_cache', default=False)

#: Use filesystem for bytecode caching
templates_use_filesystem_cache = BooleanConfigField('templates.use_filesystem_cache', default=False)


def populate_context_defaults(context):
    """Fill in context defaults."""
    try:
        context.update({
            'request': ctx.current_request,
            'active': None,
            'SERVICE_URL': IServiceProvider.get_base_url()
        })
    except AttributeError:
        # Don't raise an error if we don't have a request as it's
        # used get render_template which can get called by the message
        # broker to deliver notifications etc…
        pass


def _return_rendered_template(tmpl, context, modifier, request=None, stream=False):
    populate_context_defaults(context)
    # apply the context modifier
    if modifier is not None:
        modifier(request, context)
    retval = tmpl.stream(context) if stream else tmpl.render(context)
    template_rendered.send(template=tmpl, context=context)
    return retval


def render_template(template_name, context, modifier=None, request=None, stream=False):
    """Renders a template.  If `stream` is ``True`` the return value will be
    a Jinja template stream and not an unicode object.
    This is useful for pages with lazy generated content or huge output
    where you don't want the users to wait until the calculation ended.
    Use streaming only in those situations because it's usually slower than
    bunch processing.
    """
    tmpl = get_environment().get_template(template_name)
    return _return_rendered_template(tmpl, context, modifier, request, stream)


def render_string(source, context, modifier=None, request=None, stream=False):
    """Same arguments as `render_template` but accepts the template source
    as input rather than a filename.
    """
    tmpl = get_environment().from_string(source)
    return _return_rendered_template(tmpl, context, modifier, request, stream)


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
            context = func(request, *args, **kwargs) or {}

            # if we got no dictionary as response type we try to force
            # to return a proper Response object instead of any further process
            if not isinstance(context, dict):
                return Response.force_type(context)

            data = render_template(template_name, context, modifier=modifier,
                                   request=request, stream=stream)
            response = Response(data)
            return response
        return templated_wrapper
    return decorator


class InyokaEnvironment(Environment):
    def __init__(self):
        loaders = {}
        for resource in ctx.get_implementations(IResourceManager, instances=True):
            loaders[resource.resource_name] = FileSystemLoader(resource.templates_path)

        loader = ChoiceLoader([FileSystemLoader(ctx.cfg['templates.path']),
                               PrefixLoader(loaders)])

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
            extensions=['jinja2.ext.i18n', 'jinja2.ext.do', 'jinja2.ext.with_',
                        'jinja2.ext.autoescape'],
            auto_reload=ctx.cfg['templates.auto_reload'],
            undefined=StrictUndefined,
            cache_size=-1,
            bytecode_cache=cache_obj,
            autoescape=True
        )

        self.globals.update(
            INYOKA_REVISION=INYOKA_REVISION,
            PYTHON_VERSION='%d.%d.%d' % sys.version_info[:3],
            DEBUG=ctx.cfg['debug'],
            href=href,
        )
        self.filters.update(
            jsonencode=json.dumps,
            datetimeformat=l10n.format_datetime,
            dateformat=l10n.format_date,
            timeformat=l10n.format_time,
            timedelta=l10n.timedeltaformat,
            monthformat=l10n.format_month,
            dayformatshort=l10n.format_day_short,
            humanize=l10n.humanize_number,
        )
        self.install_gettext_translations(
            i18n.get_translations(),
            newstyle=True
        )



_jinja_env = None
_jinja_env_lock = Lock()


def get_environment():
    global _jinja_env
    with _jinja_env_lock:
        if _jinja_env is None:
            _jinja_env = InyokaEnvironment()
        return _jinja_env


@i18n.translations_reloaded.connect
def reload_environment(sender):
    get_environment().install_gettext_translations(
        i18n.get_translations(), newstyle=True
    )
