# -*- coding: utf-8 -*-
"""
    test_confirm
    ~~~~~~~~~~~~

    Unittests for the inyoka utilities.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import date, timedelta
from sqlalchemy.sql import update
from werkzeug import Client, Href
from inyoka.core.test import *
from inyoka.core.models import Confirm
from inyoka.utils.confirm import register_confirm, call_confirm, Expired


CONFIRM_LOG = []

@register_confirm('__test_store')
def _store_data(data):
    CONFIRM_LOG.append(data)

@register_confirm('__test_store2')
def _store_data2(data):
    CONFIRM_LOG.append((2, data))

def reset_log():
    del CONFIRM_LOG[:]


@refresh_database
@with_setup(reset_log)
def test_base():
    data = {'some': 'data'}
    c = Confirm('__test_store', data, 1)
    eq_(c.expires, date.today() + timedelta(days=1))
    db.session.commit()
    call_confirm(c.key)

    def _second_run():
        call_confirm(c.key)
    assert_raises(KeyError, _second_run)

    c = Confirm('__test_store2', data, 1)
    db.session.commit()
    call_confirm(c.key)

    eq_(CONFIRM_LOG, [data, (2, data)])

@refresh_database
@with_setup(reset_log)
def test_expiry():
    c = Confirm('__test_store', {}, timedelta(days=3))
    eq_(c.expires, date.today() + timedelta(days=3))
    assert_false(c.is_expired)
    db.session.commit()

    # potential validation in the model would be ok, so we must bypass this
    db.session.execute(update(Confirm.__table__, Confirm.id == 1,
                              {'expires': date(2009,1,1)}))
    c = Confirm.query.get(c.id)
    db.session.commit()
    assert_true(c.is_expired)
    assert_raises(Expired, call_confirm, c.key)

    eq_(CONFIRM_LOG, [])


@refresh_database
@raises(Exception) # may raise anything, is not intended for catching anyway
def test_duplicate():
    @register_confirm('__test_store')
    def void(data):
        pass


@refresh_database
@raises(KeyError)
def test_no_handler():
    c = Confirm('__nonexistent', {}, 1)
