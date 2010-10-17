# -*- coding: utf-8 -*-
"""
    inyoka.core.routing
    ~~~~~~~~~~~~~~~~~~~

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
import sre_constants
from inspect import ismethod
from datetime import datetime
from werkzeug.routing import Submount, Subdomain, EndpointPrefix, \
    Rule, BaseConverter, ValidationError
from werkzeug import url_quote
from werkzeug.routing import Map as BaseMap
from inyoka import Interface
from inyoka.context import ctx
from inyoka.core.exceptions import MethodNotAllowed
from inyoka.core.serializer import send_service_response
from inyoka.utils import getmembers
from inyoka.utils.urls import make_full_domain
from inyoka.utils.decorators import make_decorator, update_wrapper
from inyoka.core.config import DottedConfigField


_date_formatter_split_re = re.compile('(%.)')
_date_formatter_mapping = {
    'd': r'\d\d',
    'j': r'\d{3}',
    'm': r'\d\d',
    'U': r'\d\d',
    'w': r'\d',
    'W': r'\d\d',
    'y': r'\d\d',
    'Y': r'\d{4}',
    '%': r'%',
}

# routing specific config values
# values are in the form of `subdomain:/submount`
# if you only apply the submount use `/submount` the `:` will be completed
routing_urls_portal = DottedConfigField('routing.urls.portal', default=u':/')
routing_urls_usercp = DottedConfigField('routing.urls.usercp', default=u':/usercp')
routing_urls_news = DottedConfigField('routing.urls.news', default=u'news:/')
routing_urls_forum = DottedConfigField('routing.urls.forum', default=u'forum:/')
routing_urls_wiki = DottedConfigField('routing.urls.wiki', default=u'wiki:/')
routing_urls_paste = DottedConfigField('routing.urls.paste', default=u'paste:/')
routing_urls_planet = DottedConfigField('routing.urls.planet', default=u'planet:/')
routing_urls_event = DottedConfigField('routing.urls.event', default=u'event:/')
routing_urls_admin = DottedConfigField('routing.urls.admin', default=u'admin:/')
routing_urls_api = DottedConfigField('routing.urls.api', default=u'api:/')
# NEVER CHANGE THAT VALUE!!! TODO: Find a better solution to implement testing
# Url prefixes...
routing_urls_test = DottedConfigField('routing.urls.test', default=u'test:/')
routing_urls_static = DottedConfigField('routing.urls.static', default=u'static:/')
routing_urls_media = DottedConfigField('routing.urls.media', default=u'media:/')



def is_endpoint(value):
    return (ismethod(value) and getattr(value, 'endpoint', None) is not None)


def get_endpoint_map(map, providers, delmitter=''):
    for provider in providers:
        members = tuple(x[1] for x in getmembers(provider, is_endpoint))
        map.update(dict((delmitter.join((provider.name, m.endpoint)), m)
                                        for m in members))
    return map


class UrlMixin(object):
    """Mixin to make components able to implement own url rules."""

    #: The name of the component. Used for `href`.
    #: If `None` the url rules will be mounted to the root
    #: of the domain.
    name = None

    # The url objects, without Subdomain or EndpointPrefix,
    # inyoka takes care of it.
    url_rules = []

    # all rules are for build only, they never match
    build_only = False

    # if `True` we don't set a `EndpointPrefix`
    ignore_prefix = False

    @classmethod
    def modify_urlrules(cls, comp):
        return comp.url_rules

    @classmethod
    def get_urlmap(cls):
        cls._endpoint_map = {}
        urls = []

        for comp in ctx.get_implementations(cls, instances=True):

            # check if url rules are for build only
            if comp.build_only:
                new_map = []
                for rule in comp.url_rules:
                    rule.build_only = True
                    new_map.append(rule)
                comp.url_rules = new_map

            name = comp.name
            # Give subclasses of UrlMixin a way to further modify the rules.
            rules = cls.modify_urlrules(comp)
            if name:
                subdomain, mount = ctx.cfg['routing.urls.' + name].split(':', 1)
                if not comp.ignore_prefix:
                    prefix = name
                    rules = [EndpointPrefix('%s/' % prefix, rules)]

                val = Submount(mount, rules)
                if subdomain != '':
                    val = Subdomain(subdomain, [val])
                urls.append(val)
            else:
                urls.extend(rules)

            cls._endpoint_map.setdefault(name, {}).update(comp.get_endpoint_map())

        return urls

    @classmethod
    def get_callable_for_endpoint(cls, endpoint):
        """Return the proper callable for `endpoint`"""
        if '/' not in endpoint:
            # we assume that we have url_sections that point
            # to no name but to an empty string
            endpoint = '/' + endpoint
        parts = endpoint.split('/', 1)
        return cls._endpoint_map[parts[0]][parts[1]]

    @classmethod
    def get_base_url(cls):
        subdomain, mount = ctx.cfg['routing.urls.' + cls.name].split(':', 1)
        url = make_full_domain(subdomain, mount)
        return url

    def get_endpoint_map(self, prefix=''):
        """This method returns a dictionary with a mapping out of
        endpoint name -> bound method.

        :param prefix:  A common prefix for every endpoint.
        """
        members = tuple(x[1] for x in getmembers(self, is_endpoint))
        endpoint_map = dict((prefix + m.endpoint, m) for m in members)
        return endpoint_map


class IController(Interface, UrlMixin):
    """Interface for controllers.

    A controller is some kind of wrapper around differend
    methods handling various routing endpoints.

    Example controller implementation::

        class DummyController(IController):

            url_rules = [
                Rule('/', endpoint='index'),
                Rule('/news/<int:id>', endpoint='news')
            ]

            @view('index')
            def index_handler(self, request):
                return Response('index view')

            @view('news')
            def news_handler(self, request, id=None):
                return Response('News %s' % (id is None and 'index' or id))

    All “handlers” are registered with :func:`view` as endpoint handlers.

    """

    register_view = staticmethod(make_decorator('endpoint'))


class IServiceProvider(Interface, UrlMixin):
    """Interface for services.

    A controller is some kind of wrapper around differend
    methods handling various routing endpoints.

    Example controller implementation::

        class DummyService(IServiceProvider):

            url_rules = [
                Rule('/', endpoint='get_dummy'),
                Rule('/<int:id>', endpoint='get_dummy'),
            ]

            @service('get_dummy')
            def get_dummy(self, id=None):
                # ...

    All “handlers” are registered with :func:`service` as endpoint handlers.

    """

    name = 'api'

    #: The version of this api provider
    version = 'dev'

    #: The component this api provider belongs to (eg core, forum)
    component = 'core'

    @staticmethod
    def register_service(name, methods=('GET',), config=None):
        """Register a method as a service.

        Note that there is an alias of this method in
        :func:`~inyoka.core.routing.service`.

        :param name:    The name of the service.  Despite of `register_view`
                        this is required.
        :param methods: The HTTP methods this function can act on.  Examples:
                        GET, POST, HEAD, OPTIONS, PUT, DELETE
        """
        def decorator(func):
            def service_wrapper(self, request, *args, **kwargs):
                if request.method not in methods:
                    raise MethodNotAllowed(methods)
                ret = func(self, request, *args, **kwargs)
                return send_service_response(request, ret, config)
            service_wrapper.endpoint = name
            service_wrapper.is_service = True
            service_wrapper.valid_methods = methods
            return update_wrapper(service_wrapper, func)
        return decorator

    @classmethod
    def modify_urlrules(cls, comp):
        # Prefix the urls with /version/component
        rules = comp.url_rules
        rules = [Submount('/%s/%s' % (comp.version, comp.component), rules)]
        rules = [EndpointPrefix('%s/' % comp.component, rules)]
        return rules

    def get_endpoint_map(self, prefix=''):
        prefix = u'%s%s/' % (prefix, self.component)
        return super(IServiceProvider, self).get_endpoint_map(prefix)


view = IController.register_view
service = IServiceProvider.register_service


def href(endpoint, **values):
    """Get the URL to an endpoint.  The keyword arguments provided are used
    as URL values.  Unknown URL values are used as keyword argument.
    Additionally there are some special keyword arguments:

    `_anchor`
        This string is used as URL anchor.

    `_external`
        If set to `True` the URL will be generated with the full server name
        and `http://` prefix.
    """
    _external = values.pop('_external', False)
    _anchor = values.pop('_anchor', None)

    if hasattr(endpoint, 'get_url_values'):
        endpoint, values = endpoint.get_url_values(**values)
        _anchor = values.pop('_anchor', None)


    url = ctx.dispatcher.get_url_adapter() \
        .build(endpoint, values, force_external=_external)
    if _anchor is not None:
        url += '#' + url_quote(_anchor)
    return unicode(url)


class DateConverter(BaseConverter):
    """
    Converter for the werkzeug routing that converts date strings in URLs to
    :class:`~datetime.date` objects.

    :param map:     A :class:`werkzeug.Map` instance passed by Werkzeug.
    :param format:  A string as expected by the strftime methods. Note that only
                    date related format characters such as m and d are supported.
    """
    def __init__(self, map, format='%Y/%m/%d'):
        # convert format string to a regex so that we don't have to be greedy.
        regex = []
        for part in _date_formatter_split_re.split(format):
            if part.startswith('%'):
                if part[1] not in _date_formatter_mapping:
                    raise ValidationError('formatter not allowed for dates: %s'
                                          % part)
                regex.append(_date_formatter_mapping[part[1]])
            else:
                regex.append(re.escape(part))
        self.regex = ''.join(regex)
        self.format = format
        super(DateConverter, self).__init__(map)

    def to_python(self, value):
        """Convert `value` to a python `date` type.

        Raises :exc:`ValidationError` if a invalid format is applied.
        :param value: A valid date for :meth:`~datetime.datetime.strptime`.
        """
        try:
            return datetime.strptime(value, self.format).date()
        except (ValueError, sre_constants.error):
            raise ValidationError('strptime failed. Either you supplied an '
                                  'invalid format string or invalid data.')

    def to_url(self, value):
        """Convert to a valid quoted URL value.

        Raises :exc:`ValidationError` if a invalid object is applied.
        :param value: A valid :class:`~datetime.date` instance.
        """
        try:
            return url_quote(value.strftime(self.format))
        except sre_constants.error:
            raise ValidationError('strftime failed. Format string seems to '
                                  'be invalid.')


class Map(BaseMap):
    """Our own map implementation for hooking in some custom converters"""
    default_converters = BaseMap.default_converters.copy()
    default_converters['date'] = DateConverter
