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

class WikiTester(ViewTestSuite):
    controller = WikiController

    def test_index_redirection(self):
        ctx.cfg['wiki.index.name'] = 'my_index_page'
        r = self.get('/', follow_redirects=False)
        eq_(r.status_code, 302)
        eq_(r.location, href('wiki/show', page='my_index_page'))


        p = Page(ctx.cfg['wiki.index.name'])
        r = Revision(page=p, change_user_id=1, epoch=1, raw_text='index page')
        db.session.commit()

        p = Page.query.get(ctx.cfg['wiki.index.name'])
        r = self.get('/', follow_redirects=False)
        eq_(r.status_code, 302)
        eq_(r.location, href(p))

    def test_show(self):
        p = Page('test page', current_epoch=2)
        p2 = Page('other page')
        r1 = Revision(page=p, change_user_id=1, epoch=1, raw_text='empty')
        r2 = Revision(page=p, change_user_id=1, epoch=2, raw_text='empty')
        r3 = Revision(page=p2, change_user_id=1, epoch=1, raw_text='empty')
        db.session.add_all([p, p2, r1, r2, r3])
        db.session.commit()

        r1 = Revision.query.get(r1.id)
        r2 = Revision.query.get(r2.id)
        r3 = Revision.query.get(r3.id)

        r = self.get('/test page', follow_redirects=False)
        ok_(r.status_code in (302, 301))
        eq_(r.location, href('wiki/show', page='test_page'))

        r = self.get('/test_page')
        eq_(r.status_code, 200)

        r = self.get('/test_page/+%d' % r2.id)
        eq_(r.status_code, 200)
        #TODO: test whether r1 is accessible as mod
        #TODO: test context if it's the right revision
