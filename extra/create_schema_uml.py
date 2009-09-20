from sqlalchemy_schemadisplay import create_uml_graph
from sqlalchemy.orm import class_mapper
from inyoka.ikhaya import models as ikhaya_models
from inyoka.pastebin import models as pastebin_models
from inyoka.forum import models as forum_models
from inyoka.wiki import models as wiki_models
from inyoka.portal import user, models as portal_models
from inyoka import ikhaya, pastebin, forum, wiki, portal


models = [wiki_models, pastebin_models, ikhaya_models, forum_models]

# lets find all the mappers in our model
mappers = [class_mapper(user.User), class_mapper(user.Group)]
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
