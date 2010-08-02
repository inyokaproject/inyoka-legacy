#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy_schemadisplay import create_uml_graph, create_schema_graph
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.exc import UnmappedClassError
from inyoka.core.api import db, ctx
from inyoka.utils import flatten_iterator

models = list(flatten_iterator(x.models for x in ctx.get_implementations(db.ISchemaController, instances=True)))

# lets find all the mappers in our model
mappers = []
tables = []
for model in models:
    try:
        mappers.append(class_mapper(model))
        tables.extend(mappers[-1].tables)
    except UnmappedClassError:
        continue

# pass them to the function and set some formatting options
uml = create_uml_graph(mappers,
    show_operations=False, # not necessary in this case
    show_multiplicity_one=False # some people like to see the ones, some don't
)
uml.write_png('uml.png') # write out the file

schema = create_schema_graph(list(set(tables)))
schema.write_png('schema.png')
