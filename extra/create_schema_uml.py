# -*- coding: utf-8 -*-
from sqlalchemy_schemadisplay import create_uml_graph
from sqlalchemy.orm import class_mapper
from inyoka.core import models as core_models
from inyoka.core.auth import models as auth_models
from inyoka.news import models as news_models
from inyoka.paste import models as paste_models
from inyoka import news, paste, forum, wiki, portal


models = [paste_models, news_models, core_models, auth_models]

# lets find all the mappers in our model
mappers = [class_mapper(auth_models.User)]
for model in models:
    for cls in (getattr(model, attr) for attr in dir(model) if attr[0] != '_'):
        try:
            mappers.append(class_mapper(cls))
        except:
            pass

# pass them to the function and set some formatting options
graph = create_uml_graph(mappers,
    show_operations=False, # not necessary in this case
    show_multiplicity_one=False # some people like to see the ones, some don't
)
graph.write_png('schema.png') # write out the file
