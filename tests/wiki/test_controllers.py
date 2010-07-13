# -*- coding: utf-8 -*-
"""
    test_controllers
    ~~~~~~~~~~~~~~~~

    Unittests for the wiki.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import href, ctx
from inyoka.core.auth.models import User
from inyoka.core.test import *
from inyoka.wiki.controllers import WikiController
from inyoka.wiki.models import Page, Revision, Text


class TestWikiController(ViewTestCase):
    controller = WikiController

    def test_index_redirection(self):
        ctx.cfg['wiki.index.name'] = 'my_index_page'
        response = self.get('/', follow_redirects=False)
        self.assertRedirects(response, 'my_index_page')

        p = Page(name=ctx.cfg['wiki.index.name'])
        r = Revision(page=p, change_user_id=1, epoch=1, raw_text='index page')
        db.session.commit()

        p = Page.query.get(ctx.cfg['wiki.index.name'])
        response = self.get('/', follow_redirects=False)
        self.assertRedirects(response, ctx.cfg['wiki.index.name'])
        db.session.delete(r)
        db.session.delete(p)

    def test_show(self):
        u = User.query.first()

        p = Page.create(u'test page', change_user=u, text=u'empty')
        p.delete()
        p = Page.create(u'test page', change_user=u, text=u'empty')
        p2 = Page.create(u'other page', change_user=u, text=u'empty')

        r1, r2 = p.all_revisions
        r3 = p2.current_revision

        response = self.get('/test page', follow_redirects=False)
        self.assertRedirects(response, 'test_page')

        response = self.get('/test_page')
        self.assertResponseOK(response)

        response = self.get('/test_page/+%d' % r2.id)
        self.assertResponseOK(response)
        #TODO: test context if it's the right revision

        response = self.get('/other_page/+%d' % r1.id)
        self.assertNotFound(response)

        response = self.get('/test_page/+%d' % r1.id)
        self.assertNotFound(response)

        for obj in (r3, r2, r1, p2, p):
            db.session.delete(obj)
        db.session.commit()

        #TODO: test whether r1 is accessible as mod

    def test_edit_redirection(self):
        u = User.query.first()

        p = Page.create(u'SoMe PaGe', change_user=u, text=u'a')

        r = self.get('/some_page/+edit', follow_redirects=False)
#        self.assertRedirects(r, href('wiki/edit', page='SoMe_PaGe'))
        eq_(r.status_code, 302)
        eq_(r.location, href('wiki/edit', page='SoMe_PaGe'))

        r = self.get('/some page/+edit', follow_redirects=False)
#        self.assertRedirects(r, href('wiki/edit', page='SoMe_PaGe'))
        eq_(r.status_code, 302)
        eq_(r.location, href('wiki/edit', page='SoMe_PaGe'))

        r = self.get('/SoMe_PaGe/+edit', follow_redirects=False)
#        self.assertResponseOK(r)
        eq_(r.status_code, 200)

    def test_edit(self):
        u = User.query.first()
        p = Page.create(u'Main Page', change_user=u, text=u'a')
        response = self.get('/Main_Page/+edit')
        self.assertResponseOK(response)

        #TODO
