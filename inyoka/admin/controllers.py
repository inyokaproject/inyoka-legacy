# -*- coding: utf-8 -*-
"""
    inyoka.admin.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    The controller components for the admin app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inspect import ismethod, getmembers
from os.path import join
from werkzeug import cached_property
from inyoka.core.api import ctx, view, IController, Rule, templated
from inyoka.core.routing import Submount, EndpointPrefix

from inyoka.admin.api import IAdminProvider


#TODO: integrate services into AdminController


class AdminController(IController):

    #: The internal application name.  Do never overwrite this!
    name = 'admin'

    @property
    def providers(self):
        return ctx.get_implementations(IAdminProvider, instances=True)

    @cached_property
    def url_rules(self):
        rules = [Rule('/', endpoint='index')]
        providers = ctx.get_implementations(IAdminProvider, instances=True)
        for provider in providers:
            map = EndpointPrefix(provider.name + '/', [
                Submount('/' + provider.name, provider.url_rules)])
            rules.append(map)
        return rules

    def get_endpoint_map(self):
        """Register all view methods from remote admin providers"""

        def _predicate(value):
            return (ismethod(value) and
                    getattr(value, 'endpoint', None) is not None)

        endpoint_map = super(AdminController, self).get_endpoint_map()

        for provider in self.providers:
            members = tuple(x[1] for x in getmembers(provider, _predicate))
            endpoint_map.update(dict((join(provider.name, m.endpoint), m)
                                      for m in members))
        return endpoint_map

    @view('index')
    @templated('admin/index.html')
    def index(self, request):
        return {
            'providers': self.providers
        }
