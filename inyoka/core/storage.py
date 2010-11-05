# -*- coding: utf-8 -*-
"""
    inyoka.core.storage
    ~~~~~~~~~~~~~~~~~~~

    This module provides a simple key-based storage with database backend whose
    data is cached for increased performance. Accessing it is quite simple::

        >>> from inyoka.core.storage import storage
        >>> storage.set(u'foo', u'bar')
        >>> storage.get(u'foo')
        u'bar'
        >>> storage.set(u'bar', u'foo')
        >>> storage.get_many([u'foo', u'bar'])
        {u'foo': u'bar', u'bar': u'foo'}

    :copyright: 2007-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from sqlalchemy.exceptions import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from inyoka.core.cache import cache
from inyoka.core.database import db
from inyoka.core.models import Storage


class CachedStorage(object):
    """
    This is a dict like interface for the `Storage` model.
    It's used to store cached values also in the database.
    """

    def get(self, key, default=None, timeout=None):
        """
        Get a value from the storage.

        :param key: The key of the requested storage value
        :param default: The value that's returned if the requested key doesn't
                        exist. Defaults to None.
        :param timeout: Give up cache writing after a specific time
        """
        value = cache.get('storage/' + key)
        if value is not None:
            return value

        result = db.session.execute(
            db.select([Storage.value]).where(Storage.key == key)
        ).fetchone()

        if result is None:
            return default

        value = result[0]
        self._update_cache(key, value, timeout)
        return value

    def set(self, key, value, timeout=None):
        """
        Set a storage value.

        :param key: The key that should be changed
        :param value: The new value for the key
        :param timeout: Give up cache writing after a specific time
        """
        try:
            Storage.query.get(key)
        except NoResultFound:
            try:
                Storage(key=key, value=value)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                # ignore concurrent insertion
                return
        else:
            Storage.query.filter_by(key=key).update({'value': value})
            db.session.commit()

        self._update_cache(key, value, timeout)

    def get_many(self, keys, timeout=None):
        """
        Get many cached values with just one cache hit or database query.

        :param keys: A list of the requested keys
        :param timeout: Give up cache writing after a specific time
        """
        objects = cache.get_dict(*('storage/%s' % key for key in keys))
        values = {}
        for key, value in objects.iteritems():
            values[key[8:]] = value
        #: a list of keys that aren't yet in the cache.
        #: They are queried using a database call.
        to_fetch = [k for k in keys if values.get(k) is None]
        if to_fetch:
            # get the items that are not in cache using a database query
            query = db.select([Storage.key, Storage.value]) \
                .where(Storage.key.in_(to_fetch))

            for key, value in db.session.execute(query):
                values[key] = value
                self._update_cache(key, value, timeout)
        return values

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def _update_cache(self, key, value, timeout=None):
        cache.set('storage/%s' % key, value, timeout)


storage = CachedStorage()
