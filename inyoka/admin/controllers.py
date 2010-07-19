# -*- coding: utf-8 -*-
"""
    inyoka.admin.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    The controller components for the admin app.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inspect import ismethod
from werkzeug import cached_property
from inyoka.core.api import ctx, view, IController, Rule, templated, \
    IServiceProvider
from inyoka.core.routing import Submount, EndpointPrefix, get_endpoint_map
from inyoka.admin.api import IAdminProvider, IAdminServiceProvider
from inyoka.utils import getmembers


def context_modifier(request, context):
    context.update(
        active='admin'
    )


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
        endpoint_map = super(AdminController, self).get_endpoint_map()
        return get_endpoint_map(endpoint_map, self.providers, u'/')

    @view('index')
    @templated('admin/index.html', modifier=context_modifier)
    def index(self, request):
        return {
            'providers': self.providers
        }


class AdminServiceProvider(IServiceProvider):

    #: The version of this api provider
    version = 'dev'

    #: The component this api provider belongs to (eg core, forum)
    component = 'admin'

    @property
    def providers(self):
        return ctx.get_implementations(IAdminServiceProvider, instances=True)

    @cached_property
    def url_rules(self):
        rules = []
        providers = ctx.get_implementations(IAdminServiceProvider, instances=True)
        for provider in providers:
            map = EndpointPrefix(provider.name + '_', [
                Submount('/' + provider.name, provider.url_rules)])
            rules.append(map)
        return rules

    def get_endpoint_map(self):
        """Register all view methods from remote admin providers"""
        endpoint_map = super(AdminServiceProvider, self).get_endpoint_map()
        return get_endpoint_map(endpoint_map, self.providers, u'_')
