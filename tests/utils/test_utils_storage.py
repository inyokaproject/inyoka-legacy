#-*- coding: utf-8 -*-
"""
    test_storage
    ~~~~~~~~~~~~

    This module tests the the storage object that uses a combination of cache
    and database storing..

    :copyright: Copyright 2008 by Benjamin Wiegand.
    :license: GNU GPL.
"""
import time
from inyoka.utils.storage import storage, fetch
from inyoka.utils.cache import cache
from inyoka.utils.database import db


def _compare(key, value):
    assert value == db.session.execute(fetch, {'key': key}).fetchone()[0] == \
        cache.get('storage/' + key) == storage[key]


def test_set():
    storage['test'] = 'foo'
    storage['test'] = 'bar'
    _compare('test', 'bar')
    storage.set('test', 'boo', 1)
    _compare('test', 'boo')
    time.sleep(3)
    assert cache.get('storage/test') is None
    storage['foo'] = 'bar'
    storage['boo'] = 'far'
    assert storage.get_many(['foo', 'boo', 'nonexisting']) == {
        'foo': 'bar',
        'boo': 'far',
        'nonexisting': None
    }
