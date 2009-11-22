import random
from nose.tools import *
from werkzeug.exceptions import NotFound
from inyoka.core.database import db
from inyoka.utils.pagination import URLPagination, GETPagination




def _setup_tables(model, set_position=False):
    # create groups with different number of entries (with random IDs).
    NUMBERS = [0, 1, 3, 14, 15, 16, 30, 31, 50, 70, 80]
    groups = []
    for n in range(len(NUMBERS)):
        groups.extend([n] * NUMBERS[n])
    random.shuffle(groups)

    by_group = dict((x, []) for x in range(len(NUMBERS)))
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
    eq_(list(p._get_buttons(threshold=2)), [
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
