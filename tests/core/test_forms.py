# -*- coding: utf-8 -*-
"""
    test_forms
    ~~~~~~~~~~

    Unittests for our modifications, patches and utilities for the bureaucracy
    form library.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core.forms.utils import model_to_dict, update_model


class DummyModel(db.Model):
    __tablename__ = '__test_forms_dummy'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    value = db.Column(db.String(500))
    _hidden = db.Column(db.String(500), nullable=True)


class DummyForm(object):
    data = {'name': u'three', 'value': u'yea!'}


class TestFormsSchemaController(db.ISchemaController):
    models = [DummyModel]


class TestFormUtils(TestSuite):

    fixtures = {
        'models': [fixture(DummyModel, name=u'one', value=u'two')],
    }

    @with_fixtures('models')
    def test_model_to_dict(self, fixtures):
        obj = fixtures['models'][0]
        data = model_to_dict(obj)
        eq_(data, {'id': 1, 'name': u'one', 'value': u'two'})
        data = model_to_dict(obj, fields=('name', 'id'))
        eq_(data, {'id': 1, 'name': u'one'})
        data = model_to_dict(obj, exclude=('id',))
        eq_(data, {'name': u'one', 'value': u'two'})
        data = model_to_dict(obj, fields=('id', 'name'), exclude=('id',))
        eq_(data, {'name': u'one'})

    @with_fixtures('models')
    def test_update_model(self, fixtures):
        old = fixtures['models'][0]
        new_data = {'name': u'three', 'value': u'yea!'}
        update_model(old, new_data)
        db.session.commit()
        new = DummyModel.query.one()
        eq_(new.name, u'three')
        eq_(new.value, u'yea!')

    @with_fixtures('models')
    def test_update_model_with_includes(self, fixtures):
        old = fixtures['models'][0]
        new_data = {'name': u'three', 'value': u'yea!'}
        update_model(old, new_data, ('name',))
        new = DummyModel.query.one()
        eq_(new.name, u'three')
        eq_(new.value, u'two')

    @with_fixtures('models')
    def test_update_model_fail_silently_on_wrong_parameters(self, fixtures):
        """test that update_model fails silently on wrong parameters."""
        old = fixtures['models'][0]
        new_data = {'name': u'three', 'something wrong': u'yea!'}
        update_model(old, new_data)
        new = DummyModel.query.one()
        eq_(new.name, u'three')
        eq_(new.value, u'two')

    @with_fixtures('models')
    def test_api_bureaucracy_compatibility(self, fixtures):
        old = fixtures['models'][0]
        update_model(old, DummyForm())
        new = DummyModel.query.one()
        eq_(new.name, u'three')
        eq_(new.value, u'yea!')
