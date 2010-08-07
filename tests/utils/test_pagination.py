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
from inyoka.utils.pagination import URLPagination, GETPagination, \
    PageURLPagination


GROUP_COUNTS = [0, 1, 3, 14, 15, 16, 30, 31, 50, 70, 80]


def _setup_tables(model):
    # create groups with different number of entries (with random IDs).
    groups = []
    for n in range(len(GROUP_COUNTS)):
        groups.extend([n] * GROUP_COUNTS[n])
    random.shuffle(groups)

    by_group = dict((x, []) for x in range(len(GROUP_COUNTS)))
    for group in groups:
        elem = model(group=group)
        by_group[group].append(elem)
        db.session.add(elem)
    db.session.commit()
    return by_group


class PaginationTest1(db.Model):
    __tablename__ = '_test_utils_pagination1'

    manager = TestResourceManager

    id = db.Column(db.Integer, primary_key=True)
    group = db.Column(db.Integer)


class QueryMock(object):
    def count(self):
        return 42
    def __getslice__(self, n, m):
        return []



def fixtures():
    return _setup_tables(PaginationTest1)


@with_fixtures(fixtures)
def test_pagination_general(fixtures):
    query = PaginationTest1.query.filter_by(group=10)
    p = URLPagination(query, 1, '/entries/', per_page=15)
    eq_(list(p.query), fixtures[10][:15])
    eq_(p.total, 80)
    eq_(list(p._get_buttons()), [
        ('prev', None),
        (1, None),
        (2, '/entries/2/'),
        ('ellipsis', '/entries/!/'),
        (6, '/entries/6/'),
        ('next', '/entries/2/'),
    ])
    assert_raises(NotFound, URLPagination, query, 7, '/entries/', per_page=15)
    assert_raises(NotFound, URLPagination, query, -1, '/entries/', per_page=15)

    for group, qlen in enumerate(GROUP_COUNTS[:5]):
        query = PaginationTest1.query.filter_by(group=group)
        p = URLPagination(query, 1, per_page=15)
        eq_(p.pages, 1)
        eq_(len(p.query), qlen)
        eq_(list(p.query), fixtures[group])
        assert_raises(NotFound, URLPagination, query, 2, per_page=15)

    for group, qlen in list(enumerate(GROUP_COUNTS))[5:7]:
        query = PaginationTest1.query.filter_by(group=group)
        p = URLPagination(query, 1, per_page=15)
        eq_(p.pages, 2)
        eq_(len(p.query), 15)
        eq_(list(p.query), fixtures[group][:15])

        p = URLPagination(query, 2)
        eq_(len(p.query), qlen - 15)
        eq_(list(p.query), fixtures[group][15:])
        assert_raises(NotFound, URLPagination, query, 3, per_page=15)

    query = PaginationTest1.query.filter_by(group=7)
    p = URLPagination(query, 3, per_page=15)
    eq_(p.pages, 3)
    eq_(len(p.query), 1)
    eq_(list(p.query), fixtures[7][30:])
    p = URLPagination(query, 4, per_page=10)
    eq_(p.pages, 4)
    eq_(len(p.query), 1)
    eq_(list(p.query), fixtures[7][30:])


@with_fixtures(fixtures)
def test_button_selection(fixtures):
    query = PaginationTest1.query.filter_by(group=10)
    p = URLPagination(query, 1, per_page=15)
    eq_(list(p._get_buttons(next=False)), [
        ('prev', None),
        (1, None),
        (2, '2/'),
        ('ellipsis', '!/'),
        (6, '6/'),
    ])

    p = URLPagination(query, 2, per_page=15)
    eq_(list(p._get_buttons(prev=False)), [
        (1, '../'),
        (2, None),
        (3, '../3/'),
        ('ellipsis', '../!/'),
        (6, '../6/'),
        ('next', '../3/')
    ])

    p = URLPagination(query, 7, per_page=12)
    eq_(list(p._get_buttons()), [
        ('prev', '../6/'),
        (1, '../'),
        (2, '../2/'),
        ('ellipsis', '../!/'),
        (6, '../6/'),
        (7, None),
        ('next', None),
    ])

    p = URLPagination(query, 8, per_page=5)
    eq_(list(p._get_buttons()), [
        ('prev', '../7/'),
        (1, '../'),
        (2, '../2/'),
        ('ellipsis', '../!/'),
        (7, '../7/'),
        (8, None),
        (9, '../9/'),
        ('ellipsis', '../!/'),
        (16, '../16/'),
        ('next', '../9/'),
    ])

    p = URLPagination(query, 8, per_page=5)
    eq_(list(p._get_buttons(inner_threshold=3)), [
        ('prev', '../7/'),
        (1, '../'),
        (2, '../2/'),
        ('ellipsis', '../!/'),
        (5, '../5/'),
        (6, '../6/'),
        (7, '../7/'),
        (8, None),
        (9, '../9/'),
        (10, '../10/'),
        (11, '../11/'),
        ('ellipsis', '../!/'),
        (16, '../16/'),
        ('next', '../9/'),
    ])

    p = URLPagination(query, 8, per_page=5)
    eq_(list(p._get_buttons(left_threshold=1, right_threshold=3)), [
        ('prev', '../7/'),
        (1, '../'),
        ('ellipsis', '../!/'),
        (7, '../7/'),
        (8, None),
        (9, '../9/'),
        ('ellipsis', '../!/'),
        (14, '../14/'),
        (15, '../15/'),
        (16, '../16/'),
        ('next', '../9/'),
    ])


@with_fixtures(fixtures)
def test_urlpagination_links(fixtures):
    q = QueryMock()
    eq_(URLPagination(q, 1).make_link(1), './')
    eq_(URLPagination(q, 1).make_link(2), '2/')
    eq_(URLPagination(q, 1).make_template(), '!/')
    eq_(URLPagination(q, 2).make_link(1), '../')
    eq_(URLPagination(q, 2).make_link(2), '../2/')
    eq_(URLPagination(q, 2).make_template(), '../!/')
    eq_(URLPagination(q, 1, link='/entries/').make_link(1), '/entries/')
    eq_(URLPagination(q, 2, link='/entries/').make_link(1), '/entries/')
    eq_(URLPagination(q, 1, link='/entries/').make_link(2), '/entries/2/')
    eq_(URLPagination(q, 2, link='/entries/').make_link(2), '/entries/2/')
    eq_(URLPagination(q, 1, link='/entries/').make_template(), '/entries/!/')
    eq_(URLPagination(q, 2, link='/entries/').make_template(), '/entries/!/')
    eq_(URLPagination(q, 1, args={"a":"b"}).make_link(1), './?a=b')
    eq_(URLPagination(q, 2, args={"a":"b"}).make_link(1), '../?a=b')
    eq_(URLPagination(q, 1, args={"a":"b"}).make_link(2), '2/?a=b')
    eq_(URLPagination(q, 2, args={"a":"b"}).make_link(2), '../2/?a=b')
    eq_(URLPagination(q, 1, args={"a":"b"}).make_template(), '!/?a=b')
    eq_(URLPagination(q, 2, args={"a":"b"}).make_template(), '../!/?a=b')
    eq_(URLPagination(q, 1, link='/entries/', args={"a":"b"}).make_link(1),
        '/entries/?a=b')
    eq_(URLPagination(q, 2, link='/entries/', args={"a":"b"}).make_link(1),
        '/entries/?a=b')
    eq_(URLPagination(q, 1, link='/entries/', args={"a":"b"}).make_link(2),
        '/entries/2/?a=b')
    eq_(URLPagination(q, 2, link='/entries/', args={"a":"b"}).make_link(2),
        '/entries/2/?a=b')
    eq_(URLPagination(q, 1, link='/entries/', args={"a":"b"}).make_template(),
        '/entries/!/?a=b')
    eq_(URLPagination(q, 2, link='/entries/', args={"a":"b"}).make_template(),
        '/entries/!/?a=b')


@with_fixtures(fixtures)
def test_pageurlpagination_links(fixtures):
    q = QueryMock()
    eq_(PageURLPagination(q, 1).make_link(1), './')
    eq_(PageURLPagination(q, 1).make_link(2), 'page/2/')
    eq_(PageURLPagination(q, 1).make_template(), 'page/!/')
    eq_(PageURLPagination(q, 2).make_link(1), '../../')
    assert_true(PageURLPagination(q, 2).make_link(2) in ('../2/', '../../page/2/'))
    assert_true(PageURLPagination(q, 2).make_template() in ('../!/',
                                                       '../../page/!/'))
    eq_(PageURLPagination(q, 1, link='/e/').make_link(1), '/e/')
    eq_(PageURLPagination(q, 2, link='/e/').make_link(1), '/e/')
    eq_(PageURLPagination(q, 1, link='/e/').make_link(2), '/e/page/2/')
    eq_(PageURLPagination(q, 2, link='/e/').make_link(2), '/e/page/2/')
    eq_(PageURLPagination(q, 1, link='/e/').make_template(), '/e/page/!/')
    eq_(PageURLPagination(q, 2, args={"a":"b"}).make_link(1), '../../?a=b')
    eq_(PageURLPagination(q, 2, link='/e/', args={"a":"b"}).make_link(2),
        '/e/page/2/?a=b')


@with_fixtures(fixtures)
def test_getpagination_links(fixtures):
    q = QueryMock()
    eq_(GETPagination(q, 1).make_link(1), '?')
    eq_(GETPagination(q, 1, link=lambda: '/Example').make_link(1), '/Example')
    eq_(GETPagination(q, 1).make_link(2), '?page=2')
    eq_(GETPagination(q, 1).make_template(), '?page=!')
    eq_(GETPagination(q, 2).make_link(1), '?')
    eq_(GETPagination(q, 2).make_link(2), '?page=2')
    eq_(GETPagination(q, 2).make_template(), '?page=!')
    eq_(GETPagination(q, 1, args={'a':'b'}).make_link(1), '?a=b')
    eq_(GETPagination(q, 1, args={'a':'b'}).make_link(2), '?a=b&page=2')
    eq_(GETPagination(q, 1, args={'a':'b'}).make_template(), '?a=b&page=!')
    eq_(GETPagination(q, 2, args={'a':'b'}).make_link(1), '?a=b')
    eq_(GETPagination(q, 2, args={'a':'b'}).make_link(2), '?a=b&page=2')
    eq_(GETPagination(q, 2, args={'a':'b'}).make_template(), '?a=b&page=!')
