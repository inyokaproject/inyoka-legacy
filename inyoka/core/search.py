# -*- coding: utf-8 -*-
"""
    inyoka.core.search
    ~~~~~~~~~~~~~~~~~~

    The inyoka search system based on xapian. It uses xappy because we're lazy
    programmers who love easy APIs.

    It has support for multiple search indexes which will be stored in the
    folder determined by the config value `search.folder` (defaults to
    "search"), but you can force another location if you want.

    By default, the `portal` application creates a basic :class:`.SearchIndex` and
    offers a search controller. You can plug your data in there or create a new
    :class:`.SearchIndex` (but then you've also to create a new controller function).

    Each :class:`.SearchIndex` should have one or more :class:`.SearchProvider` associated
    with it. Each :class:`.SearchProvider` provides access to exactly one :class:`~inyoka.core.database.Model`.

    All :class:`.SearchIndex` and :class:`.SearchProvider` classes have to be registered in the
    application's :class:`~inyoka.core.resource.IResourceManager`::

        class MySearchIndex(SearchIndex):
            name = 'foo'
            ...

        class MySearchProvider(SearchProvider):
            name = 'bar'
            index = 'foo'
            ...

        class MyResourceManager(IResourceManager):
            search_indexes = [MySearchIndex()]
            search_providers = [MySearchProvider()]

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import time
from os import path
from weakref import WeakKeyDictionary
from threading import currentThread as get_current_thread
from werkzeug.utils import cached_property
import xapian
from xappy import UnprocessedDocument, Field, IndexerConnection,\
    SearchConnection
from inyoka import Interface
from inyoka.core.api import db, ctx
from inyoka.core.config import TextConfigField, IntegerConfigField
from inyoka.core.resource import IResourceManager
from itertools import ifilter


#: The name of the search database
search_index_folder = TextConfigField('search.folder', default=u'search')

#: How many objects should be displayed per page when searching?
search_count = IntegerConfigField('search.count', default=20)


_index_connection = None
_search_connections = WeakKeyDictionary()


def get_connection(path, indexer=False):
    """Get a connection to the database.

    This function reuses already existing connections.
    """
    global _index_connection, _search_connections

    _connection_attemts = 0
    while _connection_attemts <= 3:
        try:
            if indexer:
                if _index_connection is None:
                    _index_connection = IndexerConnection(path)
                connection = _index_connection
            else:
                thread = get_current_thread()
                if thread not in _search_connections:
                    _search_connections[thread] = connection = SearchConnection(path)
                else:
                    connection = _search_connections[thread]
        except xapian.DatabaseOpeningError:
            time.sleep(0.5)
            connection.reopen()
            _connection_attemts += 1
        else:
            break

    return connection


class SearchIndex(Interface):
    """
    A xapian search index.
    By default it's stored in a new folder in `search.folder`, but you can
    change this behaviour by overriding `path`.

    You've to implement `_register_fields` and to set `name` and
    `direct_search_allowed`.
    """
    #: The name of the search index. This is also used for getting
    name = None
    #: field names allowed for direct search. For some reason adding text fields
    #: here breaks direct field searching, so don't do it. TODO: Research
    #: whether this is wanted behaviour or a bug.
    direct_search_allowed = []

    @property
    def path(self):
        search_folder = ctx.cfg['search.folder']
        return path.join(search_folder, self.name)

    @cached_property
    def indexer(self):
        """
        Return an `IndexerConnection` object for this search index.
        Remember to cache the result because multiple indexers for the same
        search index can lead to problems.
        """
        indexer = get_connection(self.path, True)
        self._register_fields(indexer)
        return indexer

    @cached_property
    def searcher(self):
        """
        Return a `SearchConnection` object for this search index.
        """
        return get_connection(self.path)

    def _register_fields(self, indexer):
        """
        Register all fields relevant for indexing. Example::

            indexer.add_field_action('title', FieldActions.INDEX_FREETEXT,
                weight=5, language='en')

        See the xappy documentation for further details on how to create fields.

        Note that you've to add new `INDEX_EXACT` fields to the
        `direct_search_allowed` list to make them searchable.
        """
        raise NotImplementedError()

    @cached_property
    def providers(self):
        return IResourceManager.get_search_providers()[self.name]


class SearchProvider(Interface):
    """
    Create a class inheriting from `SearchProvider` to make your app accessible
    to the search. Register this new-created class in your ResourceManager like
    this:

    You've to implement `prepare` and `prepare_all` and to set `name` and
    `index`.
    """
    #: the name of the provider which has to be unique.
    name = None
    #: the name of the search index the provider belongs to.
    index = None

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

    def process(self, doc_ids):
        """
        Processes a list of match ids.
        By default this returns the same as `prepare` but for special cases
        you can override this method (e.g. if you just want to get the ids or
        want to have database objects instead of dictionaries).
        """
        return self.prepare(doc_ids)


class SearchIndexMapperExtension(db.MapperExtension):
    """
    This MapperExtension is for automatically push an object to the search index
    queue when it gets created, updated or deleted. As long you're using the
    SqlAlchemy models to alter the database you don't have to handle nothing
    manually.
    It's first parameter is the name of the search index, the second one is the
    name of the search provider the model belongs to.
    """
    def __init__(self, index, provider):
        self.index = index
        self.provider = provider

    def _update_index(self, mapper, connection, instance):
        from celery.execute import send_task
        send_task('inyoka.core.tasks.UpdateSearchTask',
                  [self.index, self.provider, instance.id])

    after_insert = after_update = after_delete = _update_index


def _process_result_ids(index, result_ids):
    """
    Process a list of result ids to a list of the result itselves in an
    efficient way. This function does not change the result order which is
    important for senseful searching.
    """
    results = {}
    for name, provider in IResourceManager.get_search_providers()[index].iteritems():
        # get all ids that belong to this provider
        ids = [r[1] for r in ifilter(lambda r: r[0] == name, result_ids)]
        # if there are no ids don't call the `prepare` method to avoid execution
        # of senseless queries
        if ids:
            for idx, obj in enumerate(provider.process(ids)):
                results['%s-%s' % (name, ids[idx])] = obj

    return [results['%s-%s' % (area, id)] for area, id in result_ids]


def query(index, q, **kwargs):
    """
    This function does two things simultaneously:
        - It searches the search index `index` for `q` which may be
          user-entered text.
          Xapian search syntax is allowed (e.g. author:root or title:"foo bar")
        - It tries to correct spelling mistakes in `q`

    It takes the following keyword arguments:
        - page: An integer determing which page to show. Note that xapian is
          optimised for low page numbers.
        - tags: A list of tag names used for filtering the results.
        - date_between: A tuple of two date strings. Only items created in the
          period between these dates are matched.

    As these tasks are executed remotely make sure you've started celery because
    otherwise you've to wait for a result until hell freezes over.

    The return value is a tuple containing three elements:
        - A list of the results
        - The expected total count of matches
        - If possible, a string containing a spelling-corrected version of `q`
          otherwise `None`
    """
    from celery.execute import send_task
    t1 = send_task('inyoka.core.tasks.search_query',
                   [index, q], {'filters': kwargs})
    t2 = send_task('inyoka.core.tasks.spell_correct', [index, q])

    result_ids, total = t1.get()
    results = _process_result_ids(index, result_ids)
    corrected = t2.get()

    return results, total, corrected != q and corrected or None


def find_similar(index, doc):
    """
    Find documents in the search index `index` similar the document `doc`, which
    has to be an id following the scheme "provider-id".
    """
    from celery.execute import send_task
    ids = send_task('inyoka.core.tasks.find_similar_docs', [index, doc]).get()
    return _process_result_ids(index, ids)


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
