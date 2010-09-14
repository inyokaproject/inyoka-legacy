# -*- coding: utf-8 -*-
"""
    test_config
    ~~~~~~~~~~~

    Tests for the inyoka configuration system

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
from inyoka.core.test import *
from inyoka.core.config import Configuration, IntegerConfigField, TextConfigField, \
    DottedConfigField, BooleanConfigField, ConfigField, ListConfigField


_config = None
_config_file_name = '_inyoka_config_file'
_default_values = {
    'value1': 1,
    'value2': 2
}


def _setup_config_test():
    global _config
    _config = Configuration(_config_file_name, _default_values)
    trans = _config.edit()
    trans.commit(force=True)
    _config.touch()


def _teardown_config_test():
    global _config
    if os.path.exists(_config_file_name):
        os.remove(_config_file_name)
    _config = None


@with_setup(teardown=_teardown_config_test)
def test_non_existing_config():
    conf = Configuration(_config_file_name)
    assert_false(conf.exists, False)
    eq_(conf._load_time, 0)


@with_setup(_setup_config_test, _teardown_config_test)
def test_base_config_field():
    field = ConfigField(None, 'value')
    eq_(field.get_default(), 'value')
    eq_(field.converter(), 'value')
    eq_(field(), 'value')


@with_setup(_setup_config_test, _teardown_config_test)
def test_list_config_field():
    field = ListConfigField(None, [1,2,3], IntegerConfigField(0, ''))
    eq_(field.get_default(), [1,2,3])
    eq_(field('2:3:4'), [2,3,4])
    eq_(field([99,99]), [99,99])


@with_setup(_setup_config_test, _teardown_config_test)
def test_integer_config_field():
    field = IntegerConfigField(None, 20, min_value=10)
    eq_(field.min_value, 10)
    eq_(field.get_default(), 20)
    eq_(field('20'), 20)
    eq_(field(5), 10)


@with_setup(_setup_config_test, _teardown_config_test)
def test_text_config_field():
    field = TextConfigField(None, 'text')
    eq_(field.get_default(), 'text')
    eq_(field('value'), u'value')
    eq_(field(' value   '), u'value')
    assert_true(isinstance(field('value'), unicode))


@with_setup(_setup_config_test, _teardown_config_test)
def test_dotted_config_field():
    field = DottedConfigField(None, 'default:')
    eq_(field('value'), ':value')


@with_setup(_setup_config_test, _teardown_config_test)
def test_boolean_config_field():
    field = BooleanConfigField(None, False)
    # check true states
    assert_true(field('1'))
    assert_true(field('yes'))
    assert_true(field('true'))
    assert_true(field('TrUe'))
    assert_true(field('on'))
    # everything that is not in the defined `True` values
    # is automatically false
    assert_false(field('some ugly thing'))
    # Everything that is not a string will be converted
    # to it's bool() value
    assert_true(field(25123))
    assert_false(field(0))
    # there are also defined false states
    assert_false(field('0'))
    assert_false(field('no'))
    assert_false(field('false'))
    assert_false(field('FaLse'))
    assert_false(field('off'))


@with_setup(_setup_config_test, _teardown_config_test)
def test_on_load_config_field_loading():
    assert_false('_test_runtime_value' in _config.defined_vars)
    runtime_value = TextConfigField('_test_runtime_value', default=u'yea')
    assert_true('_test_runtime_value' in _config.defined_vars)
    assert_equal(_config['_test_runtime_value'], u'yea')
