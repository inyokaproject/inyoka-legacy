# -*- coding: utf-8 -*-
"""
    inyoka.core.resource
    ~~~~~~~~~~~~~~~~~~~~

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from sqlalchemy import Table
from inyoka import Interface
from inyoka.context import ctx


class IResource(Interface):
    models = []

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
