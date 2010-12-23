# -*- coding: utf-8 -*-
"""
    inyoka.core.templating
    ~~~~~~~~~~~~~~~~~~~~~~

    Description goes here...

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import sys
import json
import functools
from pkg_resources import DefaultProvider, ResourceManager, \
    get_provider
from jinja2 import Environment, FileSystemLoader, StrictUndefined, \
    ChoiceLoader, FileSystemBytecodeCache, MemcachedBytecodeCache, \
    PackageLoader, PrefixLoader, TemplateNotFound
from jinja2.loaders import split_template_path
from inyoka import INYOKA_REVISION, l10n, i18n
from inyoka.context import ctx
from inyoka.core.http import Response
from inyoka.core.routing import href, IServiceProvider
from inyoka.core.cache import cache as inyoka_cache
from inyoka.core.config import TextConfigField, BooleanConfigField


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

#TODO: yet a hack untill we have proper information about what an app is
templates_packages_portal = TextConfigField('templates.packages.portal', default=u'inyoka.portal')
templates_packages_news = TextConfigField('templates.packages.news', default=u'inyoka.news')
templates_packages_forum = TextConfigField('templates.packages.forum', default=u'inyoka.forum')
templates_packages_wiki = TextConfigField('templates.packages.wiki', default=u'inyoka.wiki')
templates_packages_paste = TextConfigField('templates.packages.paste', default=u'inyoka.paste')
templates_packages_event = TextConfigField('templates.packages.admin', default=u'inyoka.admin')
templates_packages_planet = TextConfigField('templates.packages.planet', default=u'inyoka.planet')
templates_packages_event = TextConfigField('templates.packages.event', default=u'inyoka.event')




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
    if stream:
        return tmpl.stream(context)
    return tmpl.render(context)


def render_template(template_name, context, modifier=None, request=None, stream=False):
    """Renders a template.  If `stream` is ``True`` the return value will be
    a Jinja template stream and not an unicode object.
    This is useful for pages with lazy generated content or huge output
    where you don't want the users to wait until the calculation ended.
    Use streaming only in those situations because it's usually slower than
    bunch processing.
    """
    tmpl = jinja_env.get_template(template_name)
    return _return_rendered_template(tmpl, context, modifier, request, stream)


def render_string(source, context, modifier=None, request=None, stream=False):
    """Same arguments as `render_template` but accepts the template source
    as input rather than a filename.
    """
    tmpl = jinja_env.from_string(source)
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
            if ctx.cfg['debug']:
                response._template_context = context
            return response
        return templated_wrapper
    return decorator


class LazyPackageLoader(PackageLoader):
    """Works like the jinja2 package loader but loads packages
    lazily to not break our import system on startup.
    """

    def __init__(self, package_name, package_path='templates',
                 encoding='utf-8'):
        self.package_name = package_name
        self.encoding = encoding
        self.manager = ResourceManager()
        self.package_path = package_path

    def get_source(self, environment, template):
        provider = get_provider(self.package_name)
        pieces = split_template_path(template)
        p = '/'.join((self.package_path,) + tuple(pieces))
        if not provider.has_resource(p):
            raise TemplateNotFound(template)

        filename = uptodate = None
        if isinstance(provider, DefaultProvider):
            filename = provider.get_resource_filename(self.manager, p)
            mtime = os.path.getmtime(filename)
            def uptodate():
                try:
                    return os.path.getmtime(filename) == mtime
                except OSError:
                    return False

        source = provider.get_resource_string(self.manager, p)
        return source.decode(self.encoding), filename, uptodate

    def list_templates(self):
        provider = get_provider(self.package_name)
        path = self.package_path
        if path[:2] == './':
            path = path[2:]
        elif path == '.':
            path = ''
        offset = len(path)
        results = []
        def _walk(path):
            for filename in provider.resource_listdir(path):
                fullname = path + '/' + filename
                if provider.resource_isdir(fullname):
                    for item in _walk(fullname):
                        results.append(item)
                else:
                    results.append(fullname[offset:].lstrip('/'))
        _walk(path)
        results.sort()
        return results


class InyokaEnvironment(Environment):
    """
    Beefed up version of the jinja environment but without security features
    to improve the performance of the lookups.
    """

    def __init__(self):
        loaders = {}
        for key, package in ctx.cfg.itersection('templates.packages'):
            loaders[key.split('.')[-1]] = LazyPackageLoader(package)

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


jinja_env = InyokaEnvironment()


@i18n.translations_reloaded.connect
def reload_environment(sender):
    jinja_env.install_gettext_translations(
        i18n.get_translations(), newstyle=True
    )
