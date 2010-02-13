# -*- coding: utf-8 -*-
"""
    test_database
    ~~~~~~~~~~~~~

    Unittests for our database framework and utilities.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
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


class DatabaseTestSchemaController(db.ISchemaController):
    models = [Category]


def test_find_next_increment():
    eq_(db.find_next_increment(Category.slug, 'cat'), 'cat')

    c1 = Category(slug='cat')
    db.session.commit()

    eq_(db.find_next_increment(Category.slug, 'cat'), 'cat2')

    c2 = Category(slug='cat2')
    db.session.commit()

    eq_(db.find_next_increment(Category.slug, 'cat'), 'cat3')


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
