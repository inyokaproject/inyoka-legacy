# -*- coding: utf-8 -*-
"""
    inyoka.core.search
    ~~~~~~~~~~~~~~~~~~~

    The inyoka search system.

    For making your app accessible to the search see the `SearchProvider` class
    which you'll have to inherit.

    For performing a search query use the `query` function.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from xappy import UnprocessedDocument, Field, FieldActions
from inyoka import Interface
from inyoka.core.api import db, ctx
from inyoka.core.auth.models import User
from inyoka.core.config import TextConfigField, IntegerConfigField
from inyoka.core.resource import IResourceManager

#: The name of the search database
search_database = TextConfigField('search.database', default=u'search.db')

#: How many objects should be displayed per page when searching?
search_count = IntegerConfigField('search.count', default=20)

#: fields allowed for direct search. For some reason adding "text" / "title"
#: here breaks direct field searching, so don't do it. TODO: Research whether
#: this is wanted behaviour or a bug.
allowed_fields = ['tag', 'author', 'date']


class SearchProvider(Interface):
    """
    Create a class inheriting from `SearchProvider` to make your app accessible
    to the search. Register this new-created class in your ResourceManager like
    this:

        class MySearchProvider(SearchProvider):
            name = 'me'
            ...

        class MyResourceManager(IResourceManager):
            search_providers = [MySearchProvider]

    You've to implement `prepare` and `prepare_all` and to set `name`.
    """
    name = None

    def prepare(self, doc_ids):
        """
        This method takes a list of document ids whose data is yielded one by
        one in dictionaries that will be saved in the search index.
        If a value is a list, the corresponding key will be set multiply to all
        list items.

        Obligatory keys are:
            - id
            - title
            - link

         Optional keys are:
            - text
            - date
            - author
            - tag

        Note that the documents should be yielded in the `doc_ids` order.
        """
        raise NotImplementedError()

    def prepare_all(self):
        """
        This works like `pepare()` except that it doesn't take any parameters.
        It fetches all documents of the database in a resource-saving way and
        yields their data in dictionaries. See the documentation of the
        `prepare` method for a list of keys.
        """
        raise NotImplementedError()


class SearchIndexMapperExtension(db.MapperExtension):
    """
    This MapperExtension is for automatically push an object to the search index
    queue when it gets created, updated or deleted. As long you're using the
    SqlAlchemy models to alter the database you don't have to handle nothing
    manually.
    Its first and only parameter is the name of the search provider the model
    belongs to.
    """
    def __init__(self, provider):
        self.provider = provider

    def _update_index(self, mapper, connection, instance):
        from celery.execute import send_task
        send_task('inyoka.core.tasks.update_search_index',
                  [self.provider, instance.id])

    after_insert = after_update = after_delete = _update_index


def query(q, page=1, **kwargs):
    """
    This function does two things:
        - It searches the search index for `q` which may be user-entered text.
          Xapian search syntax is allowed (e.g. author:root or title:"foo bar")
        - It tries to correct spelling mistakes in `q`

    As these tasks are executed remotely make sure you've started celery because
    otherwise you've to wait for a result until hell freezes over.

    The return value is a tuple containing three elements:
        - A list of the results
        - The expected total count of matches
        - If possible, a string containing a spelling-corrected version of `q`
          otherwise `None`
    """
    from celery.execute import send_task
    t1 = send_task('inyoka.core.tasks.search_query', [q, page], kwargs)
    t2 = send_task('inyoka.core.tasks.spell_correct', [q])

    results = {}
    result_ids, total = t1.get()

    for name, provider in IResourceManager.get_search_providers().iteritems():
        # get all ids that belong to this provider
        ids = [r[1] for r in filter(lambda r: r[0] == name, result_ids)]
        # if there are no ids don't call the `prepare` method to avoid execution
        # of senseless queries
        if ids:
            for obj in provider.prepare(ids):
                results['%s-%s' % (name, obj['id'])] = obj

    results = [results['%s-%s' % (area, id)] for area, id in result_ids]
    corrected = t2.get()

    return results, total, corrected != q and corrected or None


def create_search_document(id, obj):
    """
    Creates a new document that can be written to the search index.
    The first parameter has to be an id following the scheme
    "searchprovider-id", the second one should be a dictionary containing the
    document's data.
    Never create the search documents manually but use this function!
    """
    doc = UnprocessedDocument()
    doc.id = id
    for key, value in obj.iteritems():
        # if the returned object is a list item we iterate over it and
        # set `key` multiply to all its children, otherwise once for
        # the value.
        for v in (value if isinstance(value, list) else [value]):
            doc.fields.append(Field(key, unicode(v)))
    return doc


def register_search_fields(indexer):
    """
    Takes an `IndexerConnection` and registers the search fields.
    """
    lang = ctx.cfg['language']
    # when adding a new INDEX_EXACT field that should be searchable, don't
    # forget to add it to the `allowed_fields` list
    indexer.add_field_action('title', FieldActions.INDEX_FREETEXT, weight=5, language=lang)
    indexer.add_field_action('text', FieldActions.INDEX_FREETEXT, language=lang, spell=True)
    indexer.add_field_action('author', FieldActions.INDEX_EXACT)
    indexer.add_field_action('tag', FieldActions.INDEX_EXACT)
    indexer.add_field_action('date', FieldActions.SORTABLE, type='date')
