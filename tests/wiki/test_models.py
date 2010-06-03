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
    p = Page(u'some name')
    eq_(p.name, u'some name')
    eq_(p.url_name, u'some_name')

    u = User.query.first()
    r = Revision(page=p, change_user=u, epoch=1)
    db.session.commit()

    eq_(None, Page.query.get('some_name'))
    eq_(p, Page.query.get('some name'))
    eq_(p, Page.query.get('sOmE nAmE'))


def test_text_raw_and_rendered():
    text1 = 'This\nis my first wiki page.'
    text1r = '<p>This\nis my first wiki page.</p>'
    text2 = 'Now\nthere is something else.'
    text2r = '<p>Now\nthere is something else.</p>'
    u = User.query.first()

    r = Revision(page=Page('foo'), change_user=u, epoch=1)
    r.raw_text = text1
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
    mock('Text._render', tracker=tracker)
    tracker.clear()
    r_.raw_text = text2
    assert_false(tracker.check('Called Text._render()'))


def test_update_current_revision():
    u = User('somebody', 'some@body.invalid')
    p1 = Page('one')
    p2 = Page('two')

    r1 = Revision(raw_text='rev 1', change_user=u, epoch=1, page=p1)
    r2 = Revision(raw_text='rev 2', change_user=u, epoch=1, page=p2)
    r3 = Revision(raw_text='rev 3', change_user=u, epoch=1, page=p1)
    r4 = Revision(raw_text='rev 4', change_user=u, epoch=1, page=p2)
    db.session.commit()

    p1 = Page.query.get(p1.id)
    p2 = Page.query.get(p2.id)

    eq_(p1.current_revision_id, r3.id)
    eq_(p1.current_revision, r3)
    eq_(p2.current_revision_id, r4.id)
    eq_(p2.current_revision, r4)

    r5 = Revision(raw_text='rev 5', change_user=u, epoch=1, page=p2)
    r6 = Revision(raw_text='rev 6', change_user=u, epoch=1, page=p2)
    db.session.commit()

    p1 = Page.query.get(p1.id)
    p2 = Page.query.get(p2.id)
    eq_(p1.current_revision, r3)
    eq_(p2.current_revision, r6)

def test_epoch_behavior():
    u = User.query.first()
    p = Page('foo', current_epoch=3)
    r1 = Revision(page=p, change_user=u, epoch=1)
    r2 = Revision(page=p, change_user=u, epoch=2)
    r3 = Revision(page=p, change_user=u, epoch=2)
    r4 = Revision(page=p, change_user=u, epoch=3)
    r5 = Revision(page=p, change_user=u, epoch=3)
    db.session.commit()

    eq_(p.all_revisions.all(), [r1, r2, r3, r4, r5])
    eq_(p.revisions.all(), [r4, r5])


def test_url_generation():
    p = Page('Page Name')
    r = Revision(page=p, change_user_id=1, epoch=1)
    db.session.commit()

    eq_(href(p), href('wiki/show', page=p.url_name))
    eq_(href(p, action='edit'), href('wiki/edit', page=p.url_name))
    eq_(href(p, action='history'), href('wiki/history', page=p.url_name))
    eq_(href(p, revision=r), href('wiki/show', page=p.url_name, revision=r.id))
    eq_(href(p, revision=r.id), href('wiki/show', page=p.url_name,
                                            revision=r.id))
    eq_(href(r), href('wiki/show', page=p.url_name, revision=r.id))

