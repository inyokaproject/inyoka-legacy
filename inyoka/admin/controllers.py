# -*- coding: utf-8 -*-
"""
    inyoka.admin.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    The controller components for the admin app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from os.path import join
from werkzeug import cached_property
from inyoka.core.api import Interface, IController, ctx, view, Rule, Response
from inyoka.core.routing import Submount, EndpointPrefix
from inyoka.utils.decorators import abstract

from inyoka.admin.api import IAdminProvider


#TODO: integrate services into AdminController


class AdminController(IController):

    #: The internal application name.  Do never overwrite this!
    name = 'admin'

    @cached_property
    def url_rules(self):
        rules = [Rule('/', endpoint='index')]
        providers = ctx.get_implementations(IAdminProvider, instances=True)
        for provider in providers:
            map = EndpointPrefix(provider.name + '/', [
                Submount('/' + provider.name, provider.url_rules)
            ])
            rules.append(map)
        return rules

    def get_endpoint_map(self):
        """Register all view methods from remote admin providers"""
        endpoint_map = {}
        providers = ctx.get_implementations(IAdminProvider, instances=True)
        for provider in providers:
            for name in dir(provider):
                obj = getattr(provider, name)
                endpoint = getattr(obj, 'endpoint', None)
                if endpoint is not None and endpoint not in endpoint_map:
                    endpoint_map[join(provider.name, endpoint)] = obj
        # register the admin controller views
        endpoint_map.update(IController.get_endpoint_map(self))
        return endpoint_map

    @view
    def index(self, request):
        return Response('Admin!')
