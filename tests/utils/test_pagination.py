# -*- coding: utf-8 -*-
"""
    test_pagination
    ~~~~~~~~~~~~~~~

    Unittests for the pagination utility.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import random
from inyoka.core.test import *
from inyoka.core.exceptions import NotFound
from inyoka.utils.pagination import URLPagination


GROUP_COUNTS = [0, 1, 3, 14, 15, 16, 30, 31, 50, 70, 80]


def _setup_tables(model, set_position=False):
    # create groups with different number of entries (with random IDs).
    groups = []
    for n in range(len(GROUP_COUNTS)):
        groups.extend([n] * GROUP_COUNTS[n])
    random.shuffle(groups)

    by_group = dict((x, []) for x in range(len(GROUP_COUNTS)))
    for group in groups:
        elem = model(group=group)
        by_group[group].append(elem)
        if set_position:
            elem.position = len(by_group[group])
        db.session.add(elem)
    db.session.commit()
    return by_group


def setup():
    global test1_by_group, test2_by_group
    test1_by_group = _setup_tables(PaginationTest1)
    test2_by_group = _setup_tables(PaginationTest2, set_position=True)


class PaginationTest1(db.Model):
    __tablename__ = '_test_utils_pagination1'
    id = db.Column(db.Integer, primary_key=True)
    group = db.Column(db.Integer)


class PaginationTest2(db.Model):
    __tablename__ = '_test_utils_pagination2'
    id = db.Column(db.Integer, primary_key=True)
    group = db.Column(db.Integer)
    position = db.Column(db.Integer)


class PaginationTestSchemaController(db.ISchemaController):
    models = [PaginationTest1, PaginationTest2]


def test_simple_pagination():
    #TODO: content tests
    query = PaginationTest1.query.filter_by(group=10)
    p = URLPagination(query, per_page=15)
    eq_(list(p.get_objects()), test1_by_group[10][:15])
    eq_(p.total, 80)
    def tester(q, p, pp):
        pagination = URLPagination(q, page=p, per_page=pp)
        return pagination.get_objects()

    assert_raises(NotFound, tester, query, 7, 15)
    assert_raises(NotFound, tester, query, -1, 15)

    for group, qlen in enumerate(GROUP_COUNTS[:5]):
        query = PaginationTest1.query.filter_by(group=group)
        p = URLPagination(query, per_page=15)
        eq_(p.pages, 1)
        eq_(len(p.get_objects()), qlen)
        assert_raises(NotFound, tester, query, 2, 15)

    for group, qlen in list(enumerate(GROUP_COUNTS))[5:7]:
        query = PaginationTest1.query.filter_by(group=group)
        p = URLPagination(query, per_page=15)
        eq_(p.pages, 2)
        eq_(len(p.get_objects()), 15)

        p = URLPagination(query, page=2)
        eq_(len(p.get_objects()), qlen - 15)
        assert_raises(NotFound, tester, query, 3, 15)

    query = PaginationTest1.query.filter_by(group=7)
    p = URLPagination(query, page=3, per_page=15)
    eq_(p.pages, 3)
    eq_(len(p.get_objects()), 1)
    p = URLPagination(query, page=4, per_page=10)
    eq_(p.pages, 4)
    eq_(len(p.get_objects()), 1)


def test_urlpagination_links():
    #TODO: test with request emulation
    class QueryMock(object):
        def count(self):
            return 42
        def __getslice__(self, n, m):
            return []
    q = QueryMock()

    eq_(URLPagination(q).link_func(1), '/')
    eq_(URLPagination(q).link_func(2), '../2/')
    eq_(URLPagination(q).make_template(1), '!/')
    eq_(URLPagination(q, page=2).link_func(1), '/')
    eq_(URLPagination(q, page=2).link_func(2), '../2/')
    eq_(URLPagination(q, page=2).make_template(2), '../!/')
