# -*- coding: utf-8 -*-
"""
    test_config
    ~~~~~~~~~~~

    Tests for the inyoka configuration system

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
from inyoka.core.test import *
from inyoka.core.config import Configuration, IntegerField, TextField, \
    DottedField, BooleanField, ConfigField


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
    os.remove(_config_file_name)
    _config = None


def test_non_existing_config():
    conf = Configuration(_config_file_name)
    assert_false(conf.exists, False)
    eq_(conf._load_time, 0)


def test_base_config_field():
    field = ConfigField('value', 'Help')
    eq_(field.get_default(), 'value')
    eq_(field.help_text, 'Help')
    eq_(field.converter(), 'value')
    eq_(field(), 'value')


def test_integer_config_field():
    field = IntegerField(20, 'Help', min_value=10)
    eq_(field.min_value, 10)
    eq_(field.get_default(), 20)
    eq_(field.help_text, 'Help')
    eq_(field('20'), 20)
    eq_(field(5), 10)


def test_text_config_field():
    field = TextField('text', 'Help')
    eq_(field.get_default(), 'text')
    eq_(field.help_text, 'Help')
    eq_(field('value'), u'value')
    eq_(field(' value   '), u'value')
    assert_true(isinstance(field('value'), unicode))


def test_dotted_config_field():
    field = DottedField('default:', 'Help')
    eq_(field('value'), ':value')


def test_boolean_config_field():
    field = BooleanField(False, 'Help')
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
