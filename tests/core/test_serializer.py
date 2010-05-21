# -*- coding: utf-8 -*-
"""
    test_serializer
    ~~~~~~~~~~~~~~~

    Unittests for the serializer system.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import datetime
from inyoka.i18n import Locale
from inyoka.core.test import *
from inyoka.core.serializer import _recursive_getattr, primitive, \
    SerializableObject


def test_recursive_getattr():
    class Foo(object):
        bar = 'test'

    class Bar(object):
        foo = Foo()

    b = Bar()
    eq_(_recursive_getattr(b, 'foo.bar'), 'test')


def test_primitive():
    class SerializableClass(SerializableObject):
        def serializable_export(self, config):
            return {'test': 'export'}
    eq_(primitive(SerializableClass()), {'test': 'export'})

    eq_(primitive(datetime(2010, 01, 01, 04, 20)),
        {'#type': 'inyoka.datetime', 'value': '2010-01-01T04:20:00Z'})
    eq_(primitive(Locale('en', 'US')), u'en_US')

    eq_(primitive({'dt': datetime(2010, 01, 04, 20, 04),
                   'str': u'some string'}),
        {'dt': {'#type': 'inyoka.datetime', 'value': '2010-01-04T20:04:00Z'},
         'str': u'some string'})
    eq_(primitive([1,2,3,4]), [1,2,3,4])
    eq_(primitive([1,2,3, datetime(2010, 01, 04, 20, 04)]),
        [1, 2, 3, {'#type': 'inyoka.datetime', 'value': '2010-01-04T20:04:00Z'}])


def test_serializable_object():
    class SerializableClass(SerializableObject):
        object_type = u'_test.class'
        public_fields = ('id', 'value')
        id = 1
        value = u'some value'
        def get_value(self):
            return u'got value'

    obj = SerializableClass()
    eq_(primitive(obj), {'#type': u'_test.class', 'id': 1,
                         'value': u'some value'})
    # test various possibilities to apply an external configuration
    eq_(primitive(obj, config={'show_type': False}),
        {'id': 1, 'value': u'some value'})
    eq_(primitive(obj, config={'_test.class': ('id',), '_test.klass': ('id', 'value')}),
        {'id': 1, '#type': u'_test.class'})

    # test special values such as callables and tuples as values
    eq_(primitive(obj, config={
        '_test.class': ('id', 'get_value', ('aliased', 'value'))
    }), {'id': 1, '#type': u'_test.class', 'get_value': u'got value',
         'aliased': u'some value'})

@raises(AssertionError)
def test_doomed_serializable_object():
    class SerializableClass(SerializableObject):
        object_type = u'_test.class'
        public_fields = None

    primitive(SerializableClass())
