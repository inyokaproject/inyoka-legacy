import random
from nose.tools import *
from werkzeug.exceptions import NotFound
from inyoka.core.database import db
from inyoka.utils.pagination import URLPagination, GETPagination


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
    __tablename__ = 'test_utils_pagination1'
    id = db.Column(db.Integer, primary_key=True)
    group = db.Column(db.Integer)


class PaginationTest2(db.Model):
    __tablename__ = 'test_utils_pagination2'
    id = db.Column(db.Integer, primary_key=True)
    group = db.Column(db.Integer)
    position = db.Column(db.Integer)


def test_simple_pagination():
    query = PaginationTest1.query.filter_by(group=10)
    p = URLPagination(query, None, '/entries/', per_page=15)
    eq_(list(p.query), test1_by_group[10][:15])
    eq_(p.total, 80)
    eq_(list(p._get_buttons()), [
        ('prev', None),
        (1, None),
        (2, '/entries/2/'),
        (3, '/entries/3/'),
        ('ellipsis', '/entries/!/'),
        (6, '/entries/6/'),
        ('next', '/entries/2/'),
    ])
    assert_raises(NotFound, URLPagination, query, 7, '/entries/', per_page=15)
    assert_raises(NotFound, URLPagination, query, 1, '/entries/', per_page=15)
    assert_raises(NotFound, URLPagination, query, -1, '/entries/', per_page=15)

    for group, qlen in enumerate(GROUP_COUNTS[:5]):
        query = PaginationTest1.query.filter_by(group=group)
        p = URLPagination(query, None, per_page=15)
        eq_(p.max_pages, 1)
        eq_(len(p.query), qlen)
        assert_raises(NotFound, URLPagination, query, 2, per_page=15)

    for group, qlen in list(enumerate(GROUP_COUNTS))[5:7]:
        query = PaginationTest1.query.filter_by(group=group)
        p = URLPagination(query, None, per_page=15)
        eq_(p.max_pages, 2)
        eq_(len(p.query), 15)

        p = URLPagination(query, 2)
        eq_(len(p.query), qlen - 15)
        assert_raises(NotFound, URLPagination, query, 3, per_page=15)

    query = PaginationTest1.query.filter_by(group=7)
    p = URLPagination(query, 3, per_page=15)
    eq_(p.max_pages, 3)
    eq_(len(p.query), 1)
    p = URLPagination(query, 4, per_page=10)
    eq_(p.max_pages, 4)
    eq_(len(p.query), 1)

    query = PaginationTest1.query.filter_by(group=10)
    p = URLPagination(query, None, per_page=15)
    eq_(list(p._get_buttons(next=False)), [
        ('prev', None),
        (1, None),
        (2, '2/'),
        (3, '3/'),
        ('ellipsis', '!/'),
        (6, '6/'),
    ])

    p = URLPagination(query, 2, per_page=15)
    eq_(list(p._get_buttons(prev=False)), [
        (1, '../'),
        (2, None),
        (3, '../3/'),
        (4, '../4/'),
        (5, '../5/'),
        (6, '../6/'),
        ('next', '../3/')
    ])

    p = URLPagination(query, 6, per_page=15)
    eq_(list(p._get_buttons()), [
        ('prev', '../5/'),
        (1, '../'),
        ('ellipsis', '../!/'),
        (4, '../4/'),
        (5, '../5/'),
        (6, None),
        ('next', None),
    ])


def test_urlpagination_links():
    class QueryMock(object):
        def count(self):
            return 42
        def __getslice__(self, n, m):
            return []
    q = QueryMock()

    eq_(URLPagination(q, None).make_link(1), './')
    eq_(URLPagination(q, None).make_link(2), '2/')
    eq_(URLPagination(q, None).make_template(), '!/')
    eq_(URLPagination(q, 2).make_link(1), '../')
    eq_(URLPagination(q, 2).make_link(2), '../2/')
    eq_(URLPagination(q, 2).make_template(), '../!/')
    eq_(URLPagination(q, None, '/entries/').make_link(1), '/entries/')
    eq_(URLPagination(q, 2, '/entries/').make_link(1), '/entries/')
    eq_(URLPagination(q, None, '/entries/').make_link(2), '/entries/2/')
    eq_(URLPagination(q, 2, '/entries/').make_link(2), '/entries/2/')
    eq_(URLPagination(q, None, '/entries/').make_template(), '/entries/!/')
    eq_(URLPagination(q, 2, '/entries/').make_template(), '/entries/!/')
    eq_(URLPagination(q, None, args={"a":"b"}).make_link(1), './?a=b')
    eq_(URLPagination(q, 2, args={"a":"b"}).make_link(1), '../?a=b')
    eq_(URLPagination(q, None, args={"a":"b"}).make_link(2), '2/?a=b')
    eq_(URLPagination(q, 2, args={"a":"b"}).make_link(2), '../2/?a=b')
    eq_(URLPagination(q, None, args={"a":"b"}).make_template(), '!/?a=b')
    eq_(URLPagination(q, 2, args={"a":"b"}).make_template(), '../!/?a=b')
    eq_(URLPagination(q, None, '/entries/', args={"a":"b"}).make_link(1),
        '/entries/?a=b')
    eq_(URLPagination(q, 2, '/entries/', args={"a":"b"}).make_link(1),
        '/entries/?a=b')
    eq_(URLPagination(q, None, '/entries/', args={"a":"b"}).make_link(2),
        '/entries/2/?a=b')
    eq_(URLPagination(q, 2, '/entries/', args={"a":"b"}).make_link(2),
        '/entries/2/?a=b')
    eq_(URLPagination(q, None, '/entries/', args={"a":"b"}).make_template(),
        '/entries/!/?a=b')
    eq_(URLPagination(q, 2, '/entries/', args={"a":"b"}).make_template(),
        '/entries/!/?a=b')
