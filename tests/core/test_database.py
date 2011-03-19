# -*- coding: utf-8 -*-
"""
    test_database
    ~~~~~~~~~~~~~

    Unittests for our database framework and utilities.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from time import sleep
from functools import partial
from inyoka.core.test import *
from inyoka.core.test.mock import mock, TraceTracker


class DatabaseTestCategory(db.Model):
    __tablename__ = '_test_database_category'

    manager = TestResourceManager

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)


class SlugGeneratorTestModel(db.Model):
    __tablename__ = '_test_database_slug_generator'
    __mapper_args__ = {'extension': db.SlugGenerator('slug', ('name', 'title'))}

    manager = TestResourceManager

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=True)
    slug = db.Column(db.String(50), nullable=False, unique=True)
    category = db.Column(db.Integer, db.ForeignKey(DatabaseTestCategory.id))
    categories = db.relationship(DatabaseTestCategory, lazy='joined', backref='sluggies')
    count = db.Column(db.Integer, default=0)


class GuidGeneratorTestModel1(db.Model):
    __tablename__ = '_test_database_guid_generator1'
    __mapper_args__ = {'extension': db.GuidGenerator('_test1')}

    manager = TestResourceManager

    id = db.Column(db.Integer, primary_key=True)
    guid = db.Column(db.String(80), unique=True)


class GuidGeneratorTestModel2(db.Model):
    __tablename__ = '_test_database_guid_generator2'
    __mapper_args__ = {'extension': db.GuidGenerator('_test2', key='slug', field='unique_id')}

    manager = TestResourceManager

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True)
    unique_id = db.Column(db.String(80), unique=True)


class DatabaseTestEntry(db.Model):
    __tablename__ = '_test_database_entry'

    manager = TestResourceManager

    entry_id = db.Column(db.Integer, primary_key=True)
    discriminator = db.Column('type', db.String(12))
    view_count = db.Column(db.Integer, default=0, nullable=False)

    __mapper_args__ = {'polymorphic_on': discriminator}


class DatabaseTestQuestion(DatabaseTestEntry):
    __tablename__ = '_test_database_question'
    __mapper_args__ = {
        'polymorphic_identity': u'question'
    }

    manager = TestResourceManager

    id = db.Column(db.Integer, db.ForeignKey(DatabaseTestEntry.entry_id), primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    answer_count = db.Column(db.Integer, default=0)


def test_find_next_increment():
    eq_(db.find_next_increment(DatabaseTestCategory.slug, u'cat'), u'cat')

    c1 = DatabaseTestCategory(slug=u'cat')
    db.session.commit()

    eq_(db.find_next_increment(DatabaseTestCategory.slug, u'cat'), u'cat2')

    c2 = DatabaseTestCategory(slug=u'cat2')
    db.session.commit()

    eq_(db.find_next_increment(DatabaseTestCategory.slug, u'cat'), u'cat3')


def test_slug_generator():
    c1 = SlugGeneratorTestModel(name=u'cat')
    db.session.commit()
    eq_(c1.slug, u'cat')
    c2 = SlugGeneratorTestModel(name=u'cat')
    db.session.commit()
    eq_(c2.slug, u'cat2')
    c3 = SlugGeneratorTestModel(name=u'cat', title=u'drei')
    db.session.commit()
    # multiple fields are joined with `sep`
    eq_(c3.slug, u'cat/drei')

    # test that models with max_length are stripped properly
    name = (u'This is just a test category with awesome features. But this string is more than 50 chars long')
    c4 = SlugGeneratorTestModel(name=name)
    db.session.commit()
    eq_(c4.slug, u'this-is-just-a-test-category-with-awesome-feat')
    c5 = SlugGeneratorTestModel(name=name)
    db.session.commit()
    eq_(c5.slug, u'this-is-just-a-test-category-with-awesome-feat2')

def test_guid_generator():
    c1 = GuidGeneratorTestModel1()
    db.session.commit()
    eq_(c1.guid, u'tag:inyoka.local,1970:inyoka/_test1/%d' % c1.id)
    c2 = GuidGeneratorTestModel2(slug=u'example')
    db.session.commit()
    eq_(c2.unique_id, u'tag:inyoka.local,1970:inyoka/_test2/example')


@set_simple_cache
def test_cached_query(cache):
    c = DatabaseTestCategory(slug=u'category')
    db.session.commit()
    # setup mock objects
    tracker = TraceTracker()
    mock('cache.set', tracker=tracker)
    tracker.clear()
    if db.driver(('sqlite', 'postgresql')):
        tester = partial(lambda: tracker.check(
            "Called cache.set("
            "    '_test/categories',"
            "    [DatabaseTestCategory(slug=u'category')],"
            "    timeout=0.5)"
        ))
    else:
        tester = partial(lambda: tracker.check(
            "Called cache.set("
            "    '_test/categories',"
            "    [DatabaseTestCategory(slug=u'category')],"
            "    timeout=0.5)"
        ))

    x = DatabaseTestCategory.query.cached('_test/categories', timeout=0.5)
    eq_(x[0].slug, c.slug)
    assert_true(tester())
    x = DatabaseTestCategory.query.cached('_test/categories', timeout=0.5)
    assert_false(tester())
    sleep(1.0)
    tracker.clear()
    x = DatabaseTestCategory.query.cached('_test/categories', timeout=0.5)
    assert_true(cache.get('_test/categories') is None)
    assert_true(tester())

    # A bug fixed in revision 842:19fb808dfa7f raised a DetachedInstanceError
    # if we accessed the cached entries twice with a lazy relationship
    c1 = SlugGeneratorTestModel(name=u'cat')
    db.session.commit()
    obj = DatabaseTestCategory.query.cached('_test/categories')[0]
    obj.sluggies
    obj = DatabaseTestCategory.query.cached('_test/categories')[0]
    obj.sluggies


def test_atomic_add():
    # We cannot test if the function is really atomic, this also depends
    # on the used database.  But we check if the results are as expected
    obj = SlugGeneratorTestModel(name=u'cat')
    db.session.commit()
    eq_(obj.count, 0)
    db.atomic_add(obj, 'count', +1)
    eq_(obj.count, 1)
    db.atomic_add(obj, 'count', -1)
    eq_(obj.count, 0)
    # check that expire is working
    db.atomic_add(obj, 'count', +1, expire=True)
    eq_(obj.count, 1)
    assert_raises(AssertionError, db.atomic_add, obj, 'count', +1, primary_key_field='slug')
    eq_(obj.count, 1)


def test_atomic_add_on_joined_tables():
    obj = DatabaseTestQuestion(title=u'some question')
    db.session.commit()
    eq_(obj.view_count, 0)
    db.atomic_add(obj, 'view_count', +1)
    eq_(obj.view_count, 1)
    db.atomic_add(obj, 'view_count', -1)
    eq_(obj.view_count, 0)
    # check that expire is working
    db.atomic_add(obj, 'view_count', +1, expire=True)
    eq_(obj.view_count, 1)
