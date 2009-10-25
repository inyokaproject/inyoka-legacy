#-*- coding: utf-8 -*-
"""
    inyoka.core.routing
    ~~~~~~~~~~~~~~~~~~~

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import re
import mimetypes
import sre_constants
from datetime import datetime
from sqlalchemy.exc import InvalidRequestError
from werkzeug.routing import Submount, Subdomain, EndpointPrefix, \
    Rule, BaseConverter, ValidationError
from werkzeug import append_slash_redirect, url_quote, wrap_file
from werkzeug.exceptions import NotFound, Forbidden
from inyoka import Component
from inyoka.core import environ
from inyoka.core.config import config
from inyoka.core.context import current_application
from inyoka.core.http import Response

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


class IController(Component):
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

    # The name of the component. Used for `href`.
    name = ''

    # The url objects, without Subdomain or Endpointprefix,
    # inyoka takes care of it.
    url_rules = []

    @classmethod
    def get_urlmap(cls):
        cls._endpoint_map = {}

        urls = []

        for comp in cls.get_components():
            url_map = {}
            for method in dir(comp):
                method = getattr(comp, method)
                endpoint = getattr(method, 'endpoint', None)
                if endpoint is not None and endpoint not in url_map:
                    url_map[endpoint] = method

            urls.append(Subdomain(config['routing.%s.subdomain' % comp.name], [
                Submount(config['routing.%s.submount' % comp.name], [
                    EndpointPrefix('%s/' % comp.name, comp.url_rules)
                ])
            ]))

            cls._endpoint_map.setdefault(comp.name, {}).update(url_map)

        return urls

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


def href(endpoint, **values):
    adapter = current_application.url_adapter
    return adapter.build(endpoint, values, force_external=True)


class DateConverter(BaseConverter):
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
