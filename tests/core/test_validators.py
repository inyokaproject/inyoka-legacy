# -*- coding: utf-8 -*-
"""
    Validator tests
    ~~~~~~~~~~~~~~~

    Some tests for the form validators

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from nose.tools import *
from inyoka.core.forms.validators import check, is_valid_slug, \
    is_valid_url_prefix, ValidationError



def test_check():
    def _false():
        def _inner(form, val):
            raise ValidationError(u'Some validation error')
        return _inner

    def _true():
        def _inner(form, val):
            pass
        return _inner


    assert_false(check(_false, 'val'))
    assert_true(check(_true, 'val'))


def test_is_valid_slug():
    assert_false(check(is_valid_slug, '/foo'))
    assert_false(check(is_valid_slug, 201*'s'))
    assert_true(check(is_valid_slug, 'foo/bar'))


def test_is_valid_url_prefix():
    f = lambda v: check(is_valid_url_prefix, v)

    # < and > are not allowed
    assert_false(f('< some cool value'))
    assert_false(f('>'))

    # no sole slash is supported
    assert_false(f('/'))

    # url prefix must start with a slash
    # and not end with a slash either
    assert_false(f('some/part'))
    assert_true(f('/some/part'))
    assert_false(f('/some/part/'))
