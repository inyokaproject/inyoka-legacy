# -*- coding: utf-8 -*-
"""
    test_database
    ~~~~~~~~~~~~~

    Unittests for our database framework and utilities.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from time import sleep
from functools import partial
from inyoka.core.test import *
from inyoka.core.cache import cache


class Category(db.Model):
    __tablename__ = '_test_database_category'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)


class SlugGeneratorTestModel(db.Model):
    __tablename__ = '_test_database_slug_generator'
    __mapper_args__ = {'extension': db.SlugGenerator('slug', ('name', 'title'))}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.Integer, db.ForeignKey(Category.id))
    categories = db.relationship(Category, lazy='joined', backref='sluggies')
    count = db.Column(db.Integer, default=0)




class Entry(db.Model):

    __tablename__ = '_test_database_entry'

    entry_id = db.Column(db.Integer, primary_key=True)
    discriminator = db.Column('type', db.String(12))
    view_count = db.Column(db.Integer, default=0, nullable=False)

    __mapper_args__ = {'polymorphic_on': discriminator}


class Question(Entry):
    __tablename__ = '_test_database_question'
    __mapper_args__ = {
        'polymorphic_identity': u'question'
    }

    id = db.Column(db.Integer, db.ForeignKey(Entry.entry_id), primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    answer_count = db.Column(db.Integer, default=0)



class DatabaseTestSchemaController(db.ISchemaController):
    models = [Category, SlugGeneratorTestModel, Entry, Question]


@refresh_database
def test_find_next_increment():
    eq_(db.find_next_increment(Category.slug, 'cat'), 'cat')

    c1 = Category(slug='cat')
    db.session.commit()

    eq_(db.find_next_increment(Category.slug, 'cat'), 'cat2')

    c2 = Category(slug='cat2')
    db.session.commit()

    eq_(db.find_next_increment(Category.slug, 'cat'), 'cat3')


@refresh_database
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


@refresh_database
def test_cached_query():
    c = Category(slug='category')
    db.session.commit()
    # setup mock objects
    mock('cache.set', tracker=tracker)
    tracker.clear()
    tester = partial(lambda: tracker.check(
        "Called cache.set("
        "    '_test/categories',"
        "    [Category(id=1, slug=u'category')],"
        "    timeout=0.5)"
    ))
    x = Category.query.cached('_test/categories', timeout=0.5)
    eq_(x[0].slug, c.slug)
    assert_true(tester())
    x = Category.query.cached('_test/categories', timeout=0.5)
    assert_false(tester())
    sleep(1.0)
    tracker.clear()
    x = Category.query.cached('_test/categories', timeout=0.5)
    assert_true(cache.get('_test/categories') is None)
    assert_true(tester())

    # A bug fixed in revision 842:19fb808dfa7f raised a DetachedInstanceError
    # if we accessed the cached entries twice with a lazy relationship
    # TODO: Test this only if caching is enabled!
    c1 = SlugGeneratorTestModel(name=u'cat')
    db.session.commit()
    obj = Category.query.cached('_test/categories')[0]
    obj.sluggies
    obj = Category.query.cached('_test/categories')[0]
    obj.sluggies


@refresh_database
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


@refresh_database
def test_atomic_add_on_joined_tables():
    obj = Question(title=u'some question')
    db.session.commit()
    eq_(obj.view_count, 0)
    db.atomic_add(obj, 'view_count', +1)
    eq_(obj.view_count, 1)
    db.atomic_add(obj, 'view_count', -1)
    eq_(obj.view_count, 0)
    # check that expire is working
    db.atomic_add(obj, 'view_count', +1, expire=True)
    eq_(obj.view_count, 1)
