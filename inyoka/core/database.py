# -*- coding: utf-8 -*-
"""
    inyoka.core.database
    ~~~~~~~~~~~~~~~~~~~~

    This module implements our interface to`SQLAlchemy`_.

    It uses scoped sessions to represent the database connection and
    implements some useful classes and functions to ease the database
    development.

    .. _database-basics:

    Basics
    ======

    The very basic operation to use the database system is to import the
    `db` module-type.

    .. data: db

        This is a pseudo module that holds all common objects, functions
        and classes to have a one-import-for-everything solution but without
        the disadvantage of a cluttered namespace as a star-import has.

    Engine
    ------

    The engine represents some kind of connection to the underlying database
    and enables us to manage transactions and such stuff.  Connection pooling
    is just another part the engine manages.

    Let's say the engine is bouncer of our database connection so that we can
    speak with a lot of databases with just one language.

    Metadata
    --------

    The core of SQLAlchemy’s query and object mapping operations are supported
    by database metadata, which is comprised of Python objects that describe
    tables and other schema-level objecs.

    Session
    -------

    The session implements some kind of instance map (not a cache!) that handles
    all of our engines and query infrastructure.  It's *the* interface we use to
    interact with the database.  The session abstracts the database transaction
    in some transparent way.  We are able to add objects to a transaction
    without touching the database and can flush these changes whenever we
    have to.  Thanks to the autoflush setting (on per default) that will be
    handled in background without any instructions.

    See :ref:`Usage <database-usage>` for more details.

    .. _database-usage:

    Usage
    =====

    … some usage examples here…

    .. _database-tricks:

    Tipps & Tricks
    ==============

    … some tipps and tricks could be mentioned here…


    .. _SQLAlchemy: <http://sqlalchemy.org>

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from __future__ import with_statement
import sys
import time
from types import ModuleType
from threading import Lock
from contextlib import contextmanager
from datetime import datetime
import sqlalchemy
from sqlalchemy import MetaData, create_engine, Table
from sqlalchemy import orm, sql, exc
from sqlalchemy.interfaces import ConnectionProxy
from sqlalchemy.orm.session import Session as SASession
from sqlalchemy.engine.url import make_url, URL
from sqlalchemy.util import to_list
from sqlalchemy.orm.interfaces import AttributeExtension
from sqlalchemy.orm.attributes import get_attribute, set_attribute
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.declarative import declarative_base, \
    DeclarativeMeta as SADeclarativeMeta, _declarative_constructor
from inyoka import Interface
from inyoka.context import ctx
from inyoka.utils import flatten_iterator
from inyoka.utils.text import get_next_increment, gen_ascii_slug
from inyoka.utils.debug import find_calling_context


_engine = None
_engine_lock = Lock()


def get_engine():
    """Creates the engine if it does not exist and returns
    the current engine.
    """
    global _engine
    with _engine_lock:
        if _engine is None:
            info = make_url(ctx.cfg['database.url'])
            # convert_unicode: Let SQLAlchemy convert all values to unicode
            #                  before we get them
            # echo:            Set the database debug level
            # pool_recycle:    Enable long-living connection pools
            # pool_timeout:    Timeout before giving up returning on a connection
            options = {'convert_unicode':   True,
                       'echo':              ctx.cfg['database.echo'],
                       'pool_recycle':      ctx.cfg['database.pool_recycle']}
            # SQLite, Access and Informix uses ThreadLocalQueuePool per default
            # and as such cannot use a timeout for pooled connections.
            if info.drivername not in ('sqlite', 'access', 'informix'):
                options.update({
                    'poolclass': QueuePool,
                    'pool_timeout': ctx.cfg['database.pool_timeout']
                })

            # if in debug mode hook in our connection debug proxy
            if ctx.cfg['database.debug']:
                options['proxy'] = ConnectionDebugProxy()

            url = SafeURL(info)
            _engine = create_engine(url, **options)
        return _engine


def refresh_engine():
    """Gets rid of the existing engine.  Useful for unittesting, use with care.
    Do not call this function if there are multiple threads accessing the
    engine.  Only do that in single-threaded test environments or console
    sessions.
    """
    global _engine
    with _engine_lock:
        session.remove()
        if _engine is not None:
            _engine.dispose()
        _engine = None


def atomic_add(obj, column, delta, expire=False, primary_key_field=None):
    """Performs an atomic add (or subtract) of the given column on the
    object.  This updates the object in place for reflection but does
    the real add on the server to avoid race conditions.  This assumes
    that the database's '+' operation is atomic.

    If `expire` is set to `True`, the value is expired and reloaded instead
    of added of the local value.  This is a good idea if the value should
    be used for reflection. The `primary_key_field` should only get passed in,
    if the mapped table is a join between two tables.
    """
    obj_mapper = orm.object_mapper(obj)
    primary_key = obj_mapper.primary_key_from_instance(obj)
    assert len(primary_key) == 1, 'atomic_add not supported for '\
        'classes with more than one primary key'

    val = orm.attributes.get_attribute(obj, column)
    if expire:
        orm.attributes.instance_state(obj).expire_attributes(
            orm.attributes.instance_dict(obj), [column])
    else:
        orm.attributes.set_committed_value(obj, column, val + delta)

    # FIXME: Does uglier work?
    for table in obj_mapper.tables:
        if column in table.c:
            break
        continue

    if primary_key_field:
        assert table.c[primary_key_field].primary_key == True, 'no primary key field'
    primary_key_field = table.c[primary_key_field] if primary_key_field is not None \
                         else obj_mapper.primary_key[0]
    stmt = sql.update(table, primary_key_field == primary_key[0], {
        column:     table.c[column] + delta
    })
    get_engine().execute(stmt)


def find_next_increment(column, string):
    """Get the next incremented string based on `column` and `string`.

    Example::

        find_next_increment(Category.slug, 'category name')
    """

    existing = session.query(column).filter(column.like('%s%%' % string)).all()
    return get_next_increment(flatten_iterator(existing), string)


def select_blocks(query, column, block_size=1000, start_with=0, max_fails=10):
    """
    Execute a query blockwise to prevent lack of memory.

    :param query: The SQLAlchemy query object.
    :param column: The SQLAlchemy column object to use for selecting.
    :param block_size: The range of objects to fetch.
    :param start_with: The object number to start with.
    :param max_fails: Sets the number of failours (empty query sets).
                      If reached fail silently.
    """
    range = (start_with, start_with + block_size)
    failed = 0
    while failed < max_fails:
        result = query.where(column.between(*range)).execute()
        i = 0
        for i, row in enumerate(result):
            yield row
        if i == 0:
            failed += 1
        else:
            failed = 0
        range = range[1] + 1, range[1] + block_size


@contextmanager
def no_autoflush(scoped_session):
    """Disable the autoflush feature temporarily.

    Use it in conjunction with the `with` statement;
    it returns a session with disabled autoflush and safely
    enables it after the `with` block.

    Example usage::

        from inyoka.core.database import db
        with no_autoflush(db.session) as sess:
            sess.execute('update core_user set (1, 'username', 'password')')

    """
    session = scoped_session()
    session.autoflush = False
    try:
        yield session
    finally:
        session.autoflush = True


class SafeURL(URL):
    """A safer url implementation, with a customized repr"""

    def __init__(self, url):
        self.url = url
        super(SafeURL, self).__init__(
            drivername=url.drivername, username=url.username,
            password=url.password, host=url.host, port=url.port,
            database=url.database, query=url.query
        )

    def __getattr__(self, attr):
        return getattr(self.url, attr)

    def __unicode__(self):
        obj = self.url
        if obj.password:
            obj.password = '***'
        return unicode(obj).replace(u':%2A%2A%2A@', u':***@', 1)

    def __str__(self):
        return self.__unicode__().encode('utf-8')


def mapper(model, table, **options):
    """A mapper that hooks in standard extensions."""
    extensions = to_list(options.pop('extension', None), [])
    options['extension'] = extensions
    # automatically register the model to the session
    old_init = getattr(model, '__init__', lambda s: None)
    def register_init(self, *args, **kwargs):
        old_init(self, *args, **kwargs)
        db.session.add(self)
    model.__init__ = register_init
    return orm.mapper(model, table, **options)


class InyokaSession(SASession):
    """Session that binds the engine as late as possible"""

    def __init__(self):
        SASession.__init__(self, get_engine(), autoflush=True,
                           autocommit=False)


metadata = MetaData()
session = orm.scoped_session(InyokaSession)


class ConnectionDebugProxy(ConnectionProxy):
    """Helps debugging the database."""

    def cursor_execute(self, execute, cursor, statement, parameters,
                       context, executemany):
        start = time.time()
        try:
            return execute(cursor, statement, parameters, context)
        finally:
            request = ctx.current_request
            if request is not None:
                request.queries.append((statement, parameters, start,
                                        time.time(), find_calling_context()))


class Query(orm.Query):
    """Default query class."""

    def get(self, pk):
        """Modify the default get to raise ``inyoka.core.database.db.NoResultFound``
        instead of returning ``None``.
        """
        result = super(Query, self).get(pk)
        if not result:
            raise orm.exc.NoResultFound()
        return result

    def dates(self, key, kind, limit=None, dt_obj=False):
        """Return all dates for which an entry exists in `column`.

        For example, dates(Article.pub_date, 'month') returns all months where an
        Article was published (a tuple (year, month) for each month).

        `kind` must be one of year, month, day, hour, minute, second.
        Inspired by Django's Models.objects.dates.
        """
        entity = self._mapper_zero()
        column = entity.columns[key]

        _kinds = ['year', 'month', 'day', 'hour', 'minute', 'second']
        idx = (_kinds.index('day') if dt_obj else _kinds.index(kind)) + 1
        query = self.session.query(column)
        result = set()
        for date in (x[0] for x in query.all()):
            if limit is not None and len(result) >= limit:
                break
            value = date.timetuple()[:idx]
            result.add(datetime(*value) if dt_obj else value)
        return result

    def cached(self, key, timeout=None):
        """Return a query result from the cache or execute the query again"""
        from inyoka.core.cache import cache
        data = cache.get(key)
        if data is None:
            data = self.all()
            cache.set(key, data, timeout=timeout)
        data = list(self.merge_result(data, load=False))
        return data

    def lightweight(self, deferred=None, lazy=None):
        """Send a lightweight query which deferes some more expensive
        things such as comment queries or even text and parser data.
        """
        args = map(db.lazyload, lazy or ()) + map(db.defer, deferred or ())
        return self.options(*args)


class ISchemaController(Interface):
    """A schemacontroller, which takes care of models and migrations.

    Only models for now…
    """

    models = []


class DeclarativeMeta(SADeclarativeMeta):
    """Our own metaclass to register all model classes
    so that we are able to hook up our model property extension
    system
    """

    _models = []

    def __init__(mcs, classname, bases, dict_):
        SADeclarativeMeta.__init__(mcs, classname, bases, dict_)
        DeclarativeMeta._models.append(mcs)


class ModelBase(object):
    """Internal baseclass for all models.  It provides some syntactic
    sugar and maps the default query property.

    We use the declarative model api from sqlalchemy.
    """
    __extendable__ = False

    def __eq__(self, other):
        equal = True
        if type(other) != type(self):
            return False
        for key in type(self)._sa_class_manager.mapper.columns.keys():
            if getattr(self, key) != getattr(other, key):
                equal = False
                break
        return equal

    def __repr__(self):
        attrs = []
        dict_ = type(self)._sa_class_manager.mapper.columns.keys()
        for key in dict_:
            if not key.startswith('_'):
                attrs.append((key, getattr(self, key)))
        return self.__class__.__name__ + '(' + ', '.join(x[0] + '=' +
                                            repr(x[1]) for x in attrs) + ')'

def _constructor(self, **kwargs):
    """A constructor that adds the model automatically to a session"""
    _declarative_constructor(self, **kwargs)


# configure the declarative base
Model = declarative_base(name='Model', cls=ModelBase,
    mapper=mapper, metadata=metadata, metaclass=DeclarativeMeta,
    constructor=_constructor)
ModelBase.query = session.query_property(Query)


class SlugGenerator(orm.MapperExtension):
    """This MapperExtension can generate unique slugs automatically.

    :param slugfield: The field the slug gets saved to.
    :param generate_from: Either a string or a list of fields to generate
                          the slug from.  If a list is applied they are
                          joined with ``sep``
    :param sep: The string to join multiple fields.  If only one field applied
                the seperator is not used.
    """

    def __init__(self, slugfield, generate_from, sep=u'/'):
        if not isinstance(generate_from, (list, tuple)):
            generate_from = (generate_from,)
        self.slugfield = slugfield
        self.generate_from = generate_from
        self.separator = sep

    def before_insert(self, mapper, connection, instance):
        fields = [get_attribute(instance, f) for f in self.generate_from]
        # filter out fields with no value as we cannot join them they are
        # not relevant for slug generation.
        fields = filter(None, fields)
        slug = self.separator.join(map(gen_ascii_slug, fields))

        set_attribute(instance, self.slugfield, find_next_increment(
                getattr(instance.__class__, self.slugfield), slug))


def init_db(**kwargs):
    tables = []

    for comp in ctx.get_implementations(ISchemaController, instances=True):
        for model in comp.models:
            if isinstance(model, Table):
                tables.append(model)
            else:
                tables.append(model.__table__)

    kwargs['tables'] = tables

    if tables:
        metadata.create_all(**kwargs)
        # some essential database things
        from inyoka.core.auth.models import User, UserProfile
        anon_name = ctx.cfg['anonymous_name']
        anon = User(anon_name, u'', u'')
        UserProfile(user=anon)
        db.session.commit()


def _make_module():
    db = ModuleType('db')
    for mod in sqlalchemy, orm:
        for key, value in mod.__dict__.iteritems():
            if key in mod.__all__:
                setattr(db, key, value)

    db.get_engine = get_engine
    db.session = session
    db.metadata = metadata
    db.mapper = mapper
    db.atomic_add = atomic_add
    db.no_autoflush = no_autoflush
    db.find_next_increment = find_next_increment
    db.Model = Model
    db.Query = Query
    db.SlugGenerator = SlugGenerator
    db.AttributeExtension = AttributeExtension
    db.ColumnProperty = orm.ColumnProperty
    db.NoResultFound = orm.exc.NoResultFound
    db.SQLAlchemyError = exc.SQLAlchemyError
    db.ISchemaController = ISchemaController
    return db

sys.modules['inyoka.core.database.db'] = db = _make_module()
