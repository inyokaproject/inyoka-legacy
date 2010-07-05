# -*- coding: utf-8 -*-
"""
    test_controllers
    ~~~~~~~~~~~~~~~~

    Unittests for the wiki.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import href, ctx
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
        p = Page(name='test page', current_epoch=2)
        p2 = Page(name='other page')
        r1 = Revision(page=p, change_user_id=1, epoch=1, raw_text='empty')
        r2 = Revision(page=p, change_user_id=1, epoch=2, raw_text='empty')
        r3 = Revision(page=p2, change_user_id=1, epoch=1, raw_text='empty')
        db.session.add_all([p, p2, r1, r2, r3])
        db.session.commit()

        r1 = Revision.query.get(r1.id)
        r2 = Revision.query.get(r2.id)
        r3 = Revision.query.get(r3.id)

        response = self.get('/test page', follow_redirects=False)
        self.assertRedirects(response, 'test_page')

        response = self.get('/test_page')
        self.assertResponseOK(response)

        response = self.get('/test_page/+%d' % r2.id)
        self.assertResponseOK(response)

        for obj in (r3, r2, r1, p2, p):
            db.session.delete(obj)
        db.session.commit()

        #TODO: test whether r1 is accessible as mod
        #TODO: test context if it's the right revision
