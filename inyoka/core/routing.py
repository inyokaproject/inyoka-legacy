#-*- coding: utf-8 -*-
"""
    inyoka.core.routing
    ~~~~~~~~~~~~~~~~~~~

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
import sre_constants
from datetime import datetime
from werkzeug.routing import Submount, Subdomain, EndpointPrefix, \
    Rule, BaseConverter, ValidationError
from werkzeug import url_quote
from werkzeug.routing import Map as BaseMap
from inyoka import Component
from inyoka.core.config import config
from inyoka.core.context import current_application
from inyoka.core.database import db


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



class UrlMixin(object):
    """Mixin to make components able to implement own url rules

    Usage::

        class MyComponent(Component, UrlMixin):

            constant = None

            def some_method(self):
                # ...


        class MyComponentImplementation(MyComponent):

            name = 'mycomponent'

            url_rules = [
                Rule('/', endpoint='foo'),
                Rule('/bar/', endpoint='bar')
            ]

    """

    # The name of the component. Used for `href`.
    name = None

    # The url objects, without Subdomain or EndpointPrefix,
    # inyoka takes care of it.
    url_rules = []

    # all rules are for build only, they never match
    build_only = False

    @classmethod
    def get_urlmap(cls):
        cls._endpoint_map = {}
        urls = []

        for comp in cls.get_components():
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

            #TODO: handle `None` component names properly
            name = comp.name
            if name:
                val = Subdomain(config['routing.%s.subdomain' % name], [
                Submount(config['routing.%s.submount' % name], [
                    EndpointPrefix('%s/' % name, comp.url_rules)
                ])])
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

            @register('index')
            def index_handler(self, request):
                return Response('index view')

            @register('news')
            def news_handler(self, request, id=None):
                return Response('News %s' % (id is None and 'index' or id))

    All “handlers” are registered with :meth:`register` as endpoint handlers.

    """

    @classmethod
    def get_servicemap(cls):
        if hasattr(cls, '_services'):
            return cls._services

        cls._services = {}
        for comp in cls.get_components():
            for method in dir(comp):
                method = getattr(comp, method)
                if getattr(method, 'service_name', None) is not None:
                    cls._services['%s.%s' % (comp.name, method.service_name)] \
                        = method
        return cls._services

    @classmethod
    def get_view(cls, endpoint):
        """Return the proper view for :attr:`endpoint`"""
        if not '/' in endpoint:
            # we assume that we have url_sections that point
            # to no name but to an empty string
            endpoint = '/' + endpoint
        parts = endpoint.split('/', 1)
        return cls._endpoint_map[parts[0]][parts[1]]

    @staticmethod
    def register(endpoint_name):
        """Register a method as an endpoint handler"""
        def wrap(func):
            func.endpoint = endpoint_name
            return func
        return wrap

    @staticmethod
    def register_service(name):
        """Register a method as a service handler"""
        def wrap(func):
            func.service_name = name
            return func
        return wrap


register = IController.register
register_service = IController.register_service


def href(endpoint, _anchor=None, _external=False, **args):
    """Get the URL to an endpoint.  The keyword arguments provided are used
    as URL values.  Unknown URL values are used as keyword argument.
    Additionally there are some special keyword arguments:

    `_anchor`
        This string is used as URL anchor.

    `_external`
        If set to `True` the URL will be generated with the full server name
        and `http://` prefix.
    """
    if isinstance(endpoint, db.Model):
        return endpoint.get_absolute_url()
    rv = current_application.url_adapter.build(endpoint, args,
        force_external=_external)
    if _anchor is not None:
        rv += '#' + url_quote(_anchor)
    return rv


class DateConverter(BaseConverter):
    """
    Converter for the werkzeug routing that converts date strings in URLs to
    `datetime.date` objects.

    :param format: A string as expected by the strftime methods. Note that only
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

    def to_python(self, value):
        try:
            return datetime.strptime(value, self.format).date()
        except (ValueError, sre_constants.error):
            raise ValidationError('strptime failed. Either you supplied an '
                                  'invalid format string or invalid data.')

    def to_url(self, value):
        try:
            return url_quote(value.strftime(self.format))
        except sre_constants.error:
            raise ValidationError('strftime failed. Format string seems to '
                                  'be invalid.')


class Map(BaseMap):
    """Our own map implementation for hooking in some custom converters"""
    import werkzeug.routing
    werkzeug.routing.DEFAULT_CONVERTERS['date'] = DateConverter
