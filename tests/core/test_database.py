# -*- coding: utf-8 -*-
"""
    test_database
    ~~~~~~~~~~~~~

    Unittests for our database framework and utilities.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *


class Category(db.Model):
    __tablename__ = '_test_database_category'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)


class DatabaseTestSchemaController(db.ISchemaController):
    models = [Category]


def test_find_next_increment():
    eq_(db.find_next_increment(Category.slug, 'cat'), 'cat')

    c1 = Category(slug='cat')
    db.session.add(c1)
    db.session.commit()

    eq_(db.find_next_increment(Category.slug, 'cat'), 'cat2')

    c2 = Category(slug='cat2')
    db.session.add(c2)
    db.session.commit()

    eq_(db.find_next_increment(Category.slug, 'cat'), 'cat3')
