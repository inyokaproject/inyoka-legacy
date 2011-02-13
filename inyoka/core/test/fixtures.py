# -*- coding: utf-8 -*-
"""
    inyoka.core.test.fixtures
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements a basic fixtures framework usable for our unittests.
    It is based on `bootalchemy <http://pypi.python.org/pypi/bootalchemy>`
    but was heavily modified to better fit Inyokas database system management.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import sys
import time
import traceback
from pprint import pformat
from functools import partial
from sqlalchemy import text
from inyoka.l10n import parse_timestamp, parse_timeonly
from inyoka.core.resource import IResourceManager
from inyoka.core.database import db, URL
from inyoka.utils.logger import logger


def _get_admin_connection(connection):
    url = connection.engine.url
    admin_engine = db.get_engine(unicode(URL(url.drivername, url.username,
        url.password, url.host, url.port, query=url.query)), force_new=True)

    return admin_engine


def create_sqlite_db(connection):
    test_database_name = connection.engine.url.database
    if not test_database_name:
        test_database_name = ':memory:'

    if test_database_name != ':memory:':
        # Erase the old test database
        logger.info('Destroying old test database "%s"...' % unicode(connection.engine.url))
        if os.access(test_database_name, os.F_OK):
            try:
                os.remove(test_database_name)
            except Exception as exc:
                logger.warning('Got an error deleting the old test database: %s\n' % exc)
    return test_database_name


def destroy_sqlite_db(connection):
    test_database_name = connection.engine.url.database
    if test_database_name and test_database_name != ":memory:":
        # Remove the SQLite database file
        if os.access(test_database_name, os.F_OK):
            try:
                os.remove(test_database_name)
            except Exception as exc:
                logger.warning('Got an error deleting the test database: %s\n' % exc)
    return test_database_name


def create_db(connection):
    """Creates the test database tables."""
    driver = connection.engine.name
    if driver == 'sqlite':
        return create_sqlite_db(connection)

    # Create the test database and connect to it. We need to autocommit
    # if the database supports it because PostgreSQL doesn't allow
    # CREATE/DROP DATABASE statements within transactions.
    def _execute(sql, *args, **kwargs):
        engine = _get_admin_connection(connection)
        engine.execute(text(sql).execution_options(autocommit=True), *args, **kwargs)

    test_database_name = connection.engine.url.database

    try:
        _execute('CREATE DATABASE %s' % test_database_name)
    except Exception as exc:
        logger.warning('Got an error creating the test database: %s\n' % exc)
        logger.info('Destroying old test database "%s"...' % unicode(connection.engine.url))
        try:
            _execute('DROP DATABASE %s' % test_database_name)
            _execute('CREATE DATABASE %s' % test_database_name)
        except Exception as exc:
            logger.warning('Got an error recreating the test database: %s\n' % exc)

    return test_database_name


def destroy_db(connection):
    """Remove the test database tables."""
    # To avoid "database is being accessed by other users" errors.
    time.sleep(1)

    driver = connection.engine.name
    if driver == 'sqlite':
        return destroy_sqlite_db(connection)

    def _execute(sql, *args, **kwargs):
        engine = _get_admin_connection(connection)
        engine.execute(text(sql).execution_options(autocommit=True), *args, **kwargs)

    try:
        _execute('DROP DATABASE %s' % connection.engine.url.database)
    except Exception:
        # The database seems to exist, fail silently.
        pass


class FixtureLoader(object):
    """This class is responsible of loading fixtures."""

    def cast(type_, cast_func, value):
        if type(value) == type_:
            return value
        else:
            return cast_func(value)

    default_casts = {
        db.Integer:int,
        db.Unicode: partial(cast, unicode, lambda x: unicode(x, 'utf-8')),
        db.Date: parse_timestamp,
        db.DateTime: parse_timestamp,
        db.Time: parse_timeonly,
        db.Float:float,
        db.Boolean: partial(cast, bool, lambda x: x.lower() not in ('f', 'false', 'no', 'n')),
        db.Binary: partial(cast, str, lambda x: x.encode('base64')),
        db.PGArray: list
    }

    def __init__(self, references=None, check_types=True):
        if references is None:
            self._references = {}
        else:
            self._references = references

        self.check_types = check_types

    def clear(self):
        """Clear the existing references."""
        self._references = {}

    def create_obj(self, cls, item):
        """Create an object with the given data"""
        return cls(**item)

    def resolve_value(self, value):
        """Resolve `value`.

        This method resolves references on columns or even whole
        objects as well as nested references.
        """
        if isinstance(value, basestring):
            if value.startswith('&'):
                return None
            elif value.startswith('*'):
                if value[1:] in self._references:
                    return self._references[value[1:]]
                else:
                    raise Exception('The pointer {val} could not be found. '
                                    'Make sure that {val} declared before '
                                    'it is used.'.format(val=value))
        elif isinstance(value, dict):
            keys = value.keys()
            if len(keys) == 1 and keys[0].startswith('!'):
                cls_name = keys[0][1:]
                items = value[keys[0]]
                cls = self.get_cls(cls_name)

                if isinstance(items, dict):
                    return self.add_cls_with_values(cls, items)
                elif isinstance(items, (list, set)):
                    return self.add_classes(cls, items)
                else:
                    raise TypeError('You can only give a nested value a list or a dict. '
                                    'You tried to feed a %s into a %s.'
                                    % (items.__class__.__name__, cls_name))
        elif isinstance(value, (list, set)):
            return type(value)([self.resolve_value(list_item) for list_item in value])

        return value

    def has_references(self, item):
        """Check if `item` has references of any kind"""
        for key, value in item.iteritems():
            if isinstance(value, basestring) and value.startswith('&'):
                return True

    def add_reference(self, key, obj):
        """Add a reference to the internal reference dictionary"""
        self._references[key[1:]] = obj

    def set_references(self, obj, item):
        """Extracts and stores the value of an object in the reference counter."""
        for key, value in item.iteritems():
            if isinstance(value, basestring) and value.startswith('&'):
                self._references[value[1:]] = getattr(obj, key)
            if isinstance(value, (list, set)):
                for i in value:
                    if isinstance(value, basestring) and i.startswith('&'):
                        self._references[value[1:]] = getattr(obj, value[1:])

    def _check_types(self, cls, obj):
        """Validate all types and cast them to better matching types if possible."""
        if not self.check_types:
            return obj
        mapper = db.class_mapper(cls)
        for table in mapper.tables:
            for key in obj.keys():
                col = table.columns.get(key, None)
                value = obj[key]
                if value is not None and col is not None and col.type is not None:
                    for type_, func in self.default_casts.iteritems():
                        if isinstance(col.type, type_):
                            obj[key] = func(value)
                            break
                if value is None and col is not None and isinstance(col.type, (db.String, db.Unicode)):
                    obj[key] = ''
        return obj

    def get_cls(self, name):
        """Try to find the right class for `name`"""
        cls = None
        models = list(IResourceManager.get_models())
        names = [m.__name__ for m in models]
        if name in names:
            cls = models[names.index(name)]

        # check that the class was found.
        if cls is None:
            raise AttributeError('Model %s not found' % name)

        return cls

    def add_cls_with_values(self, cls, values):
        """Return a new objects with resolved `values`.

        :param cls: A type to initiate.
        :param values: A dictionary with values for initialisation.
        """
        ref_name = None
        keys = values.keys()
        if len(keys) == 1 and keys[0].startswith('&') and isinstance(values[keys[0]], dict):
            ref_name = keys[0]
            values = values[ref_name] # ie. item.values[0]

        # Values is a dict of attributes and their values for any ObjectName.
        # Copy the given dict, iterate all key-values and process those with
        # special directions (nested creations or links).
        resolved_values = values.copy()
        for key, value in resolved_values.iteritems():
            resolved_values[key] = self.resolve_value(value)

        # _check_types currently does nothing (unless you call the loaded with a check_types parameter)
        resolved_values = self._check_types(cls, resolved_values)

        obj = self.create_obj(cls, resolved_values)
        db.session.add(obj)

        if ref_name:
            self.add_reference(ref_name, obj)
        if self.has_references(values):
            db.session.flush()
            self.set_references(obj, values)

        return obj

    def add_classes(self, cls, items):
        """Returns a list of the new objects.
        These objects are already in session, so you don't
        *need* to do anything with them.

        """
        objects = []
        for item in items:
            obj = self.add_cls_with_values(cls, item)
            objects.append(obj)
        return objects

    def from_list(self, data):
        """Initialize `data` in `session`.  See unittest docs for more details."""
        cls = None
        item = None
        group = None
        skip_keys = ['nocommit']
        new_data = []

        # psycopg2 raises an InternalError instance that is not inherited from
        # `Exception` and as such requires to be catched too.
        exceptions = [Exception]
        if 'postgresql' in db.get_engine().url.drivername:
            try:
                from psycopg2 import InternalError
                exceptions.append(InternalError)
            except ImportError:
                pass

        for group in data:
            for cls, items in group.iteritems():
                if cls in skip_keys:
                    continue
                if isinstance(cls, basestring) and cls not in skip_keys:
                    cls = self.get_cls(cls)
                new_data.append({cls.__name__: self.add_classes(cls, items)})
            if 'nocommit' not in group:
                try:
                    db.session.commit()
                except exceptions:
                    self.log_error(sys.exc_info()[2], data, cls, item)
                    db.session.rollback()

        return new_data

    def log_error(self, e, data, cls, item):
        msg = (u'error occured while loading fixture data with output:\n%s\n'
               u'class: %s\nitem: %s\n%s') % (pformat(data), cls, item, traceback.format_exc(e))
        logger.error(msg)
