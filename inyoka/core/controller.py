#-*- coding: utf-8 -*-
"""
    inyoka.core.controller
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug.routing import Submount, EndpointPrefix
from inyoka import Component


class IController(Component):
    # The prefix, will get prefix.domain, or domain/prefix
    # depending on the config.
    url_section = ''

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

            urls.append(Submount('/%s' % comp.url_section,
                             [EndpointPrefix('%s/' % comp.url_section,
                                             comp.url_rules)]
                        ))
            cls._endpoint_map.setdefault(comp.url_section, {}).update(url_map)

        return urls

    @classmethod
    def get_view(cls, endpoint):
        parts = endpoint.split('/', 1)
        return cls._endpoint_map[parts[0]][parts[1]]

    @staticmethod
    def register(endpoint_name):
        def wrap(func):
            func.endpoint = endpoint_name
            return func
        return wrap

register = IController.register
