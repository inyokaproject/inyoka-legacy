# -*- coding: utf-8 -*-
"""
    inyoka.core.database
    ~~~~~~~~~~~~~~~~~~~~

    This module provides the database interface inyoka uses.

    It uses scoped sessions to represent the database connection and
    implements some useful classes and functions to ease the database
    development.

    This module must never import application code so that migrations

    The default session shutdown happens in the application handler in
    :mod:`inyoka.application`.

    To use this model you normally only need to import the `db` object.
    It implements a wrapper for all commonly used sqlalchemy classes,
    functions as well as our own utilities.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from __future__ import with_statement
import os
import sys
import time
from os import path
from types import ModuleType
from contextlib import contextmanager
from sqlalchemy import MetaData, String, create_engine
from sqlalchemy.orm import scoped_session, create_session, Query as QueryBase, \
        mapper as sqla_mapper
from sqlalchemy.orm.scoping import _ScopedExt
from sqlalchemy.orm.interfaces import AttributeExtension
from sqlalchemy.pool import NullPool
from sqlalchemy.interfaces import ConnectionProxy
from sqlalchemy.engine.url import make_url, URL
from sqlalchemy.util import to_list, get_cls_kwargs
from inyoka.core.api import get_application, href
from inyoka.core.config import config


if sys.platform == 'win32':
    _timer = time.clock
else:
    _timer = time.time


def _create_engine():
    info = make_url(config['database_uri'])
    options = {'convert_unicode': True,
               'echo': config['database_debug'],
               'pool_recycle': 300}
    if info.drivername == 'mysql':
        info.query.setdefault('charset', 'utf8')
    elif info.drivername == 'sqlite':
        # disable polling for sqlite
        options.update({
            #'poolclass': NullPool, <-- This locks our sqlite databases in test runs…
            #                           but don't ask why…
            'connect_args': {'timeout': 30}
        })
    url = SafeURL(info)
    return create_engine(url, **options)


def session_mapper(scoped_session):
    def mapper(cls, *arg, **kwargs):
        extension_args = dict((arg, kwargs.pop(arg))
                              for arg in get_cls_kwargs(_ScopedExt)
                              if arg in kwargs)
        kwargs['extension'] = extension = to_list(kwargs.get('extension', []))
        if extension_args:
            extension.append(scoped_session.extension.configure(**extension_args))
        else:
            extension.append(scoped_session.extension)

        if not 'query' in cls.__dict__:
            cls.query = scoped_session.query_property(Query)

        return sqla_mapper(cls, *arg, **kwargs)
    return mapper


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

#: initiate the database
_engine = _create_engine()
_metadata = MetaData(bind=_engine)

_session = scoped_session(lambda: create_session(_engine, autoflush=True,
                                                 autocommit=False))


class Query(QueryBase):
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


class Model(object):
    """
    Internal baseclass for all models. It provides some syntactic
    sugar and mapps the default query property.
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


def _make_module():
    import sqlalchemy
    from sqlalchemy import orm

    db = ModuleType('db')
    for mod in sqlalchemy, orm:
        for key, value in mod.__dict__.iteritems():
            if key in mod.__all__:
                setattr(db, key, value)

    db.File = File
    db.engine = _engine
    db.session = _session
    db.Model = Model
    db.Query = Query
    db.AttributeExtension = AttributeExtension
    db.metadata = _metadata
    db.mapper = session_mapper(_session)
    return db

sys.modules['inyoka.utils.database.db'] = db = _make_module()
