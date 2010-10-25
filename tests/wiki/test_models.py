# -*- coding: utf-8 -*-
"""
    test_models
    ~~~~~~~~~~~

    Unittests for the wiki.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import datetime
from inyoka.core.api import href, ctx
from inyoka.core.auth.models import User
from inyoka.core.test import *
from inyoka.wiki.models import Page, Revision, Text, PageExists, PageDeleted


@refresh_database
def test_page_name_conversion_and_get_by_name():
    p = Page(name=u'some name')
    eq_(p.name, u'some name')
    eq_(p.url_name, u'some_name')

    u = User.query.first()
    r = Revision(page=p, change_user=u, epoch=1)
    db.session.commit()

    eq_(None, Page.query.get(u'some_name'))
    eq_(p, Page.query.get(u'some name'))
    eq_(p, Page.query.get(u'sOmE nAmE'))


@refresh_database
def test_text_raw_and_rendered():
    text1 = u'This\nis my first wiki page.'
    text1r = u'<p>This\nis my first wiki page.</p>'
    text2 = u'Now\nthere is something else.'
    text2r = u'<p>Now\nthere is something else.</p>'
    u = User.query.first()

    r = Page.create(u'foo', change_user=u, text=u'a').current_revision
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
    mock(u'Text._render', tracker=tracker)
    tracker.clear()
    r_.raw_text = text2
    assert_false(tracker.check(u'Called Text._render()'))



@refresh_database
def test_page_create_and_edit():
    u = User.query.first()
    u2 = User(username=u'user 2')
    revs = []

    p = Page.create(u'one', change_user=u, change_comment=u'hi', text=u'bla')
    assert_raises(PageExists, Page.create, u'one', change_user=u)

    eq_(p.current_revision.raw_text, u'bla')
    eq_(p.current_revision.epoch, 1)
    eq_(p.current_epoch, 1)
    revs.append(p.current_revision)

    p.edit(change_user=u2, text=u'spam', change_date=datetime(2000,1,1))
    eq_(p.current_revision.raw_text, u'spam')
    eq_(p.current_revision.change_date, datetime(2000,1,1))
    eq_(p.current_revision.epoch, 1)
    eq_(p.current_epoch, 1)
    revs.append(p.current_revision)

    p.delete()
    eq_(p.current_epoch, 2)
    assert_raises(PageDeleted, p.edit, change_user=u, text=u'foo')

    p_ = p
    p = Page.create(u'one', change_user=u2, change_comment=u'new', text=u'wb')
    ok_(p is p_)
    eq_(p.current_epoch, 2)
    eq_(p.current_revision.raw_text, u'wb')
    eq_(p.current_revision.epoch, 2)
    eq_(p.current_revision.change_user, u2)
    eq_(p.current_revision.change_comment, u'new')
    revs.append(p.current_revision)

    eq_(p.revisions.all(), [p.current_revision])
    eq_(p.all_revisions.all(), revs)
    eq_([r for r in revs if r.in_current_epoch], [p.current_revision])

    p.edit(change_user=u, text=u'muh')
    revs.append(p.current_revision)
    p.edit(change_user=u, text=u'buh')
    revs.append(p.current_revision)
    eq_(p.revisions.all(), revs[-3:])

    p.delete()
    eq_(p.revisions.all(), [])

    Page.create_or_edit(u'one', change_user=u, text=u'muh')
    eq_(p.current_epoch, 3)
    eq_(p.current_revision.raw_text, u'muh')
    Page.create_or_edit(u'one', change_user=u, text=u'miau')
    eq_(p.current_epoch, 3)
    eq_(p.current_revision.raw_text, u'miau')



@refresh_database
def test_epoch_behavior():
    u = User.query.first()
    p = Page(name=u'foo', current_epoch=3)
    r1 = Revision(page=p, change_user=u, epoch=1)
    r2 = Revision(page=p, change_user=u, epoch=2)
    r3 = Revision(page=p, change_user=u, epoch=2)
    r4 = Revision(page=p, change_user=u, epoch=3)
    r5 = Revision(page=p, change_user=u, epoch=3)
    db.session.commit()

    eq_(set(p.all_revisions.all()), set([r1, r2, r3, r4, r5]))
    eq_(set(p.revisions.all()), set([r4, r5]))


@refresh_database
def test_url_generation():
    p = Page(name=u'Page Name')
    r = Revision(page=p, change_user_id=1, epoch=1)
    db.session.commit()

    eq_(href(p), href('wiki/show', page=p.url_name))
    eq_(href(p, action='edit'), href('wiki/edit', page=p.url_name))
    eq_(href(p, action='history'), href('wiki/history', page=p.url_name))
    eq_(href(p, revision=r), href('wiki/show', page=p.url_name, revision=r.id))
    eq_(href(p, revision=r.id), href('wiki/show', page=p.url_name,
                                            revision=r.id))
    eq_(href(r), href('wiki/show', page=p.url_name, revision=r.id))

def test_exists():
    assert_false(Page.query.exists(u'no such page'))

    p = Page(name=u'example Page')
    r = Revision(page=p, change_user_id=1, epoch=1)
    db.session.commit()

    ok_(Page.query.exists(u'example Page'))
    ok_(Page.query.exists(u'ExAmplE pAgE'))
    assert_false(Page.query.exists(u'example_page'))
