# -*- coding: utf-8 -*-
"""
    inyoka.core.database
    ~~~~~~~~~~~~~~~~~~~~

    This module implements our interface to `SQLAlchemy <http://sqlalchemy.org>`_.

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

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from __future__ import with_statement
import sys
from types import ModuleType
from threading import Lock
from contextlib import contextmanager
from sqlalchemy import MetaData, create_engine
from sqlalchemy import orm, sql
from sqlalchemy.engine.url import make_url, URL
from sqlalchemy.util import to_list
from sqlalchemy.orm.interfaces import AttributeExtension
from sqlalchemy.ext.declarative import declarative_base
from inyoka.core.config import config


_engine = None
_engine_lock = Lock()


def get_engine():
    """Creates the engine if it does not exist and returns
    the current engine.
    """
    global _engine
    with _engine_lock:
        if _engine is None:
            info = make_url(config['database_url'])
            # convert_unicode: Let SQLAlchemy convert all values to unicode
            #                  before we get them
            # echo:            Set the database debug level
            # pool_recycle:    Enable long-living connection pools
            options = {'convert_unicode': True,
                       'echo': config['database_debug'],
                       'pool_recycle': -1}
            if info.drivername == 'mysql':
                info.query.setdefault('charset', 'utf8')
            elif info.drivername == 'sqlite':
                # enable longer timeouts for sqlite
                options.update({
                    'connect_args': {'timeout': 30}
                })
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


def atomic_add(obj, column, delta, expire=False):
    """Performs an atomic add (or subtract) of the given column on the
    object.  This updates the object in place for reflection but does
    the real add on the server to avoid race conditions.  This assumes
    that the database's '+' operation is atomic.

    If `expire` is set to `True`, the value is expired and reloaded instead
    of added of the local value.  This is a good idea if the value should
    be used for reflection.
    """
    sess = orm.object_session(obj) or session
    mapper = orm.object_mapper(obj)
    pk = mapper.primary_key_from_instance(obj)
    assert len(pk) == 1, 'atomic_add not supported for classes with ' \
                         'more than one primary key'

    val = orm.attributes.get_attribute(obj, column)
    if expire:
        orm.attributes.instance_state(obj).expire_attributes([column])
    else:
        orm.attributes.set_committed_value(obj, column, val + delta)

    table = mapper.tables[0]
    stmt = sql.update(table, mapper.primary_key[0] == pk[0], {
        column:     table.c[column] + delta
    })
    sess.execute(stmt)


def select_blocks(query, pk, block_size=1000, start_with=0, max_fails=10):
    """
    Execute a query blockwise to prevent lack of memory.

    :param query: The SQLAlchemy query object.
    :param pk: The SQLAlchemy column object to use for selecting.
    :param block_size: The range of objects to fetch.
    :param start_with: The object number to start with.
    :param max_fails: Sets the number of failours (empty query sets).
                      If reached fail silently.
    """
    range = (start_with, start_with + block_size)
    failed = 0
    while failed < max_fails:
        result = query.where(pk.between(*range)).execute()
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
    """Disable the autoflush feature temporary

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
    return orm.mapper(model, table, **options)


#: initiate the database
metadata = MetaData(get_engine())
session = orm.scoped_session(lambda: orm.create_session(
    get_engine(), autoflush=True, autocommit=False
))


class Query(orm.Query):
    """Default query class."""

    def dates(self, key, kind):
        """
        Return all dates for which an entry exists in `column`.

        For example, dates(Article.pub_date, 'month') returns all months where an
        Article was published (a tuple (year, month) for each month).

        `kind` must be one of year, month, day, hour, minute, second.
        Inspired by Django's Models.objects.dates.
        """
        entity = self._mapper_zero()
        column = entity.columns[key]

        KINDS = ['year', 'month', 'day', 'hour', 'minute', 'second']
        i = KINDS.index(kind) + 1
        q = self.session.query(column)
        result = set()
        for date in (x[0] for x in q.all()):
            result.add(date.timetuple()[:i])
        return result

    def lightweight(self, deferred=None, lazy=None):
        """Send a lightweight query which deferes some more expensive
        things such as comment queries or even text and parser data.
        """
        args = map(db.lazyload, lazy or ()) + map(db.defer, deferred or ())
        return self.options(*args)


class ModelBase(object):
    """Internal baseclass for all models.  It provides some syntactic
    sugar and maps the default query property.

    We use the declarative model api from sqlalchemy.
    """

    def __init__(self, *mixed, **kwargs):
        # some syntactic sugar. It allows us to initialize
        # a model just via the constructor without create
        # one in the “real” model.
        dict_ = type(self)._sa_class_manager.keys()
        for key, value in kwargs.items():
            if not key.startswith('_') and key in dict_:
                setattr(self, key, value)
            else:
                raise AttributeError('Cannot set attribute which is' +
                                     'not column in mapped table: %s' % (key,))

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

# configure the declarative base
Model = declarative_base(name='Model', cls=ModelBase, mapper=mapper,
                         metadata=metadata)
ModelBase.query = session.query_property(Query)


def _make_module():
    import sqlalchemy
    from sqlalchemy import orm

    db = ModuleType('db')
    for mod in sqlalchemy, orm:
        for key, value in mod.__dict__.iteritems():
            if key in mod.__all__:
                setattr(db, key, value)

    db.engine = get_engine()
    db.session = session
    db.metadata = metadata
    db.mapper = mapper
    db.Model = Model
    db.Query = Query
    db.AttributeExtension = AttributeExtension
    return db

sys.modules['inyoka.core.database.db'] = db = _make_module()
