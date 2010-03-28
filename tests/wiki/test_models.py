# -*- coding: utf-8 -*-
"""
    test_models
    ~~~~~~~~~~~

    Unittests for the wiki.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import href, ctx
from inyoka.core.auth.models import User
from inyoka.core.test import *
from inyoka.wiki.models import Page, Revision, Text

def test_page_name_conversion_and_get_by_name():
    p = Page(u'some_name')
    eq_(p.name, u'some name')
    eq_(p.url_name, u'some_name')

    p = Page(u'some name')
    eq_(p.name, u'some name')
    eq_(p.url_name, u'some_name')

    db.session.rollback()
    db.session.add(p)
    db.session.commit()

    eq_(p, Page.query.get('some_name'))
    eq_(p, Page.query.get('some name'))

def test_text_raw_and_rendered():
    text1 = 'This\nis my first wiki page.'
    text1r = 'This<br />\nis my first wiki page.'
    text2 = 'Now\nthere is something else.'
    text2r = 'Now<br />\nthere is something else.'
    u = User.query.first()

    r = Revision(page=Page('foo'), change_user=u)
    r.raw_text = text1
    assert_raises(ValueError, setattr, r, 'rendered_text', 'something')
    eq_(r.raw_text, text1)
    eq_(r.rendered_text, text1r)
    r.raw_text = text2
    eq_(r.raw_text, text2)
    eq_(r.rendered_text, text2r)
    db.session.commit()

    r_ = Revision.query.get(r.id)
    eq_(r_.raw_text, text2)
    eq_(r_.rendered_text, text2r)

    # assert that we don't call the rerender method when not required
    mock('Text._rerender', tracker=tracker)
    tracker.clear()
    r_.raw_text = text2
    assert_false(tracker.check('Called Text._rerender()'))

def test_update_current_revision():
    u = User('somebody', 'some@body.invalid')
    p1 = Page('one')
    p2 = Page('two')

    r1 = Revision(raw_text='rev 1', change_user=u, page=p1)
    r2 = Revision(raw_text='rev 2', change_user=u, page=p2)
    r3 = Revision(raw_text='rev 3', change_user=u, page=p1)
    r4 = Revision(raw_text='rev 4', change_user=u, page=p2)
    db.session.commit()

    p1 = Page.query.get(p1.id)
    p2 = Page.query.get(p2.id)
    eq_(p1.current_revision_id, r3.id)
    eq_(p1.current_revision, r3)
    eq_(p2.current_revision_id, r4.id)
    eq_(p2.current_revision, r4)

    r5 = Revision(raw_text='rev 5', change_user=u, page=p2)
    r6 = Revision(raw_text='rev 6', change_user=u, page=p2)
    db.session.commit()

    p1 = Page.query.get(p1.id)
    p2 = Page.query.get(p2.id)
    eq_(p1.current_revision, r3)
    eq_(p2.current_revision, r6)
