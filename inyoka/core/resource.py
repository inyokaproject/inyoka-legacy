# -*- coding: utf-8 -*-
"""
    inyoka.core.resource
    ~~~~~~~~~~~~~~~~~~~~

    The resource system of Inyoka.  This abstract interface implements
    various ways to interact with the Inyoka core.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import sys
from sqlalchemy import Table
from werkzeug import cached_property
from inyoka import Interface
from inyoka.context import ctx


def _get_package_path(name):
    """Returns the path to a package or cwd if that cannot be found."""
    try:
        return os.path.abspath(os.path.dirname(sys.modules[name].__file__))
    except (KeyError, AttributeError):
        return os.getcwd()


class IResourceManager(Interface):
    """An interface to load resource specific items such as models, templates
    or even components.  This allow you to define your application behaviour
    more deeply without getting in our (or inyokas...) way.

    """

    #: The name of the package or module this IResourceManager is located.
    #: If it's None it defaults to the current module of the IResourceManager.
    package_name = None

    #: The short name to identify resource specific paths and features.
    short_name = None

    #: List all models here to get them registered with the database
    #: subsystem.  Models not listed won't be recognized by structure
    #: changing operations such as initial table creation.
    models = []

    #: List all search indexes here.
    search_indexes = []

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
    def get_search_indexes(cls):
        """
        Generates a name -> `SearchIndex` mapping of all search indexes.
        """
        dct = {}
        for component in ctx.get_implementations(cls, instances=True):
            for index in component.search_indexes:
                dct[index.name] = index
        return dct

    @classmethod
    def get_search_providers(cls):
        """
        Generates a dictionary whose keys are the search index names and whose
        values are dictionaries of the search providers belonging to them.
        """
        dct = {}
        for component in ctx.get_implementations(cls, instances=True):
            for provider in component.search_providers:
                dct.setdefault(provider.index, {})
                dct[provider.index][provider.name] = provider
        return dct

    @property
    def resource_name(self):
        module = sys.modules[self.__module__]
        return self.short_name or u'.'.join(module.__package__.split('.')[1:])

    @property
    def root_path(self):
        """Where is the app root located?"""
        return _get_package_path(self.package_name or self.__module__)

    @property
    def has_static_folder(self):
        """This is `True` if the package bound object's container has a
        folder named ``'static'``.
        """
        return os.path.isdir(os.path.join(self.root_path, 'static'))

    @property
    def templates_path(self):
        """The path to the templates folder."""
        return os.path.join(self.root_path, 'templates')

    def open_resource(self, resource):
        """Opens a resource from the application's resource folder.  To see
        how this works, consider the following folder structure::

            /myapplication.py
            /schemal.sql
            /static
                /style.css
            /templates
                /layout.html
                /index.html

        If you want to open the `schema.sql` file you would do the
        following::

            with app.open_resource('schema.sql') as f:
                contents = f.read()
                do_something_with(contents)

        :param resource: the name of the resource.  To access resources within
                         subfolders use forward slashes as separator.
        """
        return open(os.path.join(self.root_path, resource), 'rb')
