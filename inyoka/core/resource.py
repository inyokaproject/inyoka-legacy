# -*- coding: utf-8 -*-
"""
    inyoka.core.resource
    ~~~~~~~~~~~~~~~~~~~~

    The resource system of Inyoka.  This abstract interface implements
    various ways to interact with the Inyoka core.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from sqlalchemy import Table
from inyoka import Interface
from inyoka.context import ctx


class IResourceManager(Interface):
    """An interface to load resource specific items such as models, templates
    or even components.  This allow you to define your application behaviour
    more deeply without getting in our (or inyokas...) way.

    """

    #: List all models here to get them registered with the database
    #: subsystem.  Models not listed won't be recognized by structure
    #: changing operations such as initial table creation.
    models = []
    #: List all search providers here to register them, otherwise their data
    #: won't be indexed.
    search_providers = []

    @classmethod
    def get_models(cls, tables=False):
        """Generator that yields all registered models.  Yields tables
        if `tables` is set to True.
        """
        for component in ctx.get_implementations(cls, instances=True):
            for model in component.models:
                is_table = isinstance(model, Table)
                if is_table and not tables:
                    continue

                if is_table and tables:
                    yield model
                else:
                    yield model.__table__ if tables else model

    @classmethod
    def get_search_providers(cls):
        dct = {}
        for component in ctx.get_implementations(cls, instances=True):
            for provider in component.search_providers:
                dct[provider.name] = provider
        return dct
