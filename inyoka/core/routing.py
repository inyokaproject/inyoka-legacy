#-*- coding: utf-8 -*-
"""
    inyoka.core.routing
    ~~~~~~~~~~~~~~~~~~~

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sre_constants
import re
from datetime import datetime
from werkzeug.routing import Submount, Subdomain, EndpointPrefix, \
    Rule as BaseRule, BaseConverter, ValidationError
from werkzeug import url_quote
from inyoka import Component
from inyoka.utils.urls import make_full_domain

#XXX: temporary to check if the routing stuff works until ente has finished
#     working on config ;-)
#from inyoka.core.config import config

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

config = {
    'routing.portal.subdomain': '',
    'routing.portal.submount': '/',
    'routing.news.subdomain': 'news',
    'routing.news.submount': '/',
    'routing.calendar.subdomain': '',
    'routing.calendar.submount': '/calendar',
    'base_domain_name': 'inyoka.local:5000',
}


class IController(Component):
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

#            urls.append(Submount('/%s' % comp.url_section,
#                             [EndpointPrefix('%s/' % comp.url_section,
#                                             comp.url_rules)]
#                        ))
#            urls.append(Subdomain(make_full_domain(config['routing.%s.subdomain' % comp.name]), [
            urls.append(Subdomain(config['routing.%s.subdomain' % comp.name], [
                Submount(config.get('routing.%s.submount' % comp.name, '/'), [
                    EndpointPrefix('%s/' % comp.name, comp.url_rules)
                ])
            ]))

            cls._endpoint_map.setdefault(comp.name, {}).update(url_map)

        return urls

    @classmethod
    def get_view(cls, endpoint):
        if not '/' in endpoint:
            # we assume that we have url_sections that point
            # to no name but to an empty string
            endpoint = '/' + endpoint
        parts = endpoint.split('/', 1)
        return cls._endpoint_map[parts[0]][parts[1]]

    @staticmethod
    def register(endpoint_name):
        def wrap(func):
            func.endpoint = endpoint_name
            return func
        return wrap

register = IController.register


def href(endpoint, **values):
    adapter = application.url_adapter
    if adapter is None:
        #TODO: build a better pseudo adapter
        adapter = application.url_map.bind(config['base_domain_name'])
    return adapter.build(endpoint, values, force_external=True)


class Rule(BaseRule):
    def __gt__(self, endpoint):
        self.endpoint = endpoint
        return self


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
