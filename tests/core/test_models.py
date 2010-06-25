# -*- coding: utf-8 -*-
"""
    test_models
    ~~~~~~~~~~~

    Tests for the core models and model mixins.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core.mixins import RevisionedModelMixin
from inyoka.core.auth.models import User


class FancyModel(db.Model, RevisionedModelMixin):
    __tablename__ = '_test_core_models_fancy_model'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    code = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey(id), nullable=True)
    children = db.relationship('FancyModel', cascade='all',
        primaryjoin=parent_id == id,
        backref=db.backref('parent', remote_side=[id]))

    def __unicode__(self):
        return '#%s' % self.id


class CoreTestSchemaController(db.ISchemaController):
    models = [FancyModel]


class TestRevisionedModelMixin(TestSuite):

    fixtures = {
        'models': [
            fixture(FancyModel, user_id=1, code=u'some code'),
            fixture(FancyModel, user_id=2, code=u'Some Code', parent_id=1),
            fixture(FancyModel, user_id=2, code=u'some Code', parent_id=2)]
    }

    @with_fixtures('models')
    def test_resolve_root(self, fixtures):
        eq_(FancyModel.resolve_root(1).id, 1)
        eq_(FancyModel.resolve_root(2).id, 1)
        eq_(FancyModel.resolve_root(3).id, 1)

    @with_fixtures('models')
    def test_fetch_replies(self, fixtures):
        root, second, last = fixtures['models']
        eq_(root.fetch_replies(), [second])
        eq_(second.fetch_replies(), [last])
        eq_(last.fetch_replies(), [])

    @with_fixtures('models')
    def test_compare_to(self, fixtures):
        root, second, last = fixtures['models']
        eq_(root.compare_to(second, 'code'),
            u'--- #1 \n+++ #2 \n@@ -1,1 +1,1 @@\n-some code\n+Some Code')
        eq_(root.compare_to(last, 'code'),
            u'--- #1 \n+++ #3 \n@@ -1,1 +1,1 @@\n-some code\n+some Code')
        eq_(second.compare_to(last, 'code'),
            u'--- #2 \n+++ #3 \n@@ -1,1 +1,1 @@\n-Some Code\n+some Code')
