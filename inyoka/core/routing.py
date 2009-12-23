# -*- coding: utf-8 -*-
"""
    inyoka.core.routing
    ~~~~~~~~~~~~~~~~~~~

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
import types
import sre_constants
from datetime import datetime
from functools import update_wrapper
from werkzeug.routing import Submount, Subdomain, EndpointPrefix, \
    Rule, BaseConverter, ValidationError
from werkzeug import url_quote
from werkzeug.routing import Map as BaseMap
from inyoka import Component
from inyoka.core.context import ctx


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

_function_types = (types.FunctionType, types.MethodType)


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
    def get_urlmap(cls):
        cls._endpoint_map = {}
        urls = []

        for comp in ctx.get_component_instances(cls):
            url_map = {}

            # check if url rules are for build only
            if cls.build_only:
                new_map = []
                for rule in comp.url_rules:
                    rule.build_only = True
                    new_map.append(rule)
                comp.url_rules = new_map

            for name in dir(comp):
                method = getattr(comp, name)
                endpoint = getattr(method, 'endpoint', None)
                if endpoint is not None and endpoint not in url_map:
                    url_map[endpoint] = method

            name = comp.name
            if name:
                domain, mount = ctx.cfg['routing.urls.' + name].split(':', 1)
                if comp.ignore_prefix:
                    rules = comp.url_rules
                else:
                    rules = [EndpointPrefix('%s/' % name, comp.url_rules)]
                val = Subdomain(domain, [Submount(mount, rules)])
                urls.append(val)
            else:
                val = comp.url_rules
                urls.extend(val)

            cls._endpoint_map.setdefault(name, {}).update(url_map)

        return urls


class IController(Component, UrlMixin):
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

    @classmethod
    def get_servicemap(cls):
        if hasattr(cls, '_services'):
            return cls._services

        cls._services = {}
        for comp in ctx.get_component_instances(cls):
            for method in dir(comp):
                method = getattr(comp, method)
                if getattr(method, 'service_name', None) is not None:
                    cls._services['%s.%s' % (comp.name, method.service_name)] \
                        = method
        return cls._services

    @classmethod
    def get_view(cls, endpoint):
        """Return the proper view for :attr:`endpoint`"""
        if '/' not in endpoint:
            # we assume that we have url_sections that point
            # to no name but to an empty string
            endpoint = '/' + endpoint
        parts = endpoint.split('/', 1)
        return cls._endpoint_map[parts[0]][parts[1]]

    def _wrapped(attr):
        """Return a method usable as a multifunctional decorator
        to make methods available under some alias.

        :param attr: A string determining what attribute will be set
                     to the alias value.
        """
        def _wrapper(func=None, alias=None):
            """Decorator to register `alias` to `func`."""
            def _proxy(func):
                if alias is None:
                    setattr(func, attr, func.__name__)
                else:
                    setattr(func, attr, alias)
                return func

            if isinstance(func, _function_types):
                # @register_view
                return update_wrapper(_proxy, func)(func)
            elif func is None:
                # @register_view()
                return update_wrapper(_proxy, func)
            elif isinstance(func, basestring):
                # @register_view('alias')
                alias = func
                return _proxy
        return _wrapper

    register_view = staticmethod(_wrapped('endpoint'))
    register_service = staticmethod(_wrapped('service_name'))



view = IController.register_view
service = IController.register_service


def href(endpoint, **args):
    """Get the URL to an endpoint.  The keyword arguments provided are used
    as URL values.  Unknown URL values are used as keyword argument.
    Additionally there are some special keyword arguments:

    `_anchor`
        This string is used as URL anchor.

    `_external`
        If set to `True` the URL will be generated with the full server name
        and `http://` prefix.
    """
    _anchor = args.pop('_anchor', None)
    _external = args.pop('_external', False)

    from inyoka.core.database import db
    if isinstance(endpoint, db.Model):
        return endpoint.get_absolute_url()
    ret = ctx.dispatcher.url_adapter.build(endpoint, args,
        force_external=_external)
    if _anchor is not None:
        ret += '#' + url_quote(_anchor)
    return ret


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
    import werkzeug.routing
    werkzeug.routing.DEFAULT_CONVERTERS['date'] = DateConverter
