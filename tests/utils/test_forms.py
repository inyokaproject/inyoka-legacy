# -*- coding: utf-8 -*-
"""
    test_forms
    ~~~~~~~~~~

    Unittests for our modifications, patches and utilities for the bureaucracy
    form library.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import MultiDict
from inyoka.core.test import *
from inyoka.core.exceptions import BadRequest
from inyoka.utils.csrf import check_request, get_csrf_token
from inyoka.utils.forms import model_to_dict, update_model, Form
from inyoka.portal.controllers import PortalController
from wtforms import TextField


class DummyModel(db.Model):
    __tablename__ = '__test_forms_dummy'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    value = db.Column(db.String(500))
    _hidden = db.Column(db.String(500), nullable=True)


class DummyForm(object):
    data = {'name': u'three', 'value': u'yea!'}


class DummyForm2(Form):
    name = TextField(u'name')


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
    def test_api_compatibility(self, fixtures):
        old = fixtures['models'][0]
        update_model(old, DummyForm())
        new = DummyModel.query.one()
        eq_(new.name, u'three')
        eq_(new.value, u'yea!')


class CsrfTester(ViewTestSuite):

    controller = PortalController

    def test_csrf_protection_success(self):
        request = self.get_new_request()
        form = DummyForm2(request.form)
        assert_true(form.validate())

    @raises(BadRequest)
    def test_csrf_protection_failure(self):
        req = self.get_new_request(path='/login', method='POST', data={'csrf_token':'invalid'})
        get_csrf_token(req)
        check_request(req)

    def check_token_set_on_session(self):
        req = self.get_new_request()
        token = get_csrf_token(req)
        eq_(token, req.session['csrf_token'])
