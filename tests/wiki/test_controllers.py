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
        r = self.get('/', follow_redirects=False)
        eq_(r.status_code, 404)

        p = Page(ctx.cfg['wiki.index.name'])
        r = Revision(page=p, change_user_id=1, raw_text='index page')
        db.session.commit()

        p = Page.query.get(ctx.cfg['wiki.index.name'])
        r = self.get('/', follow_redirects=False)
        eq_(r.status_code, 302)
        eq_(r.location, href(p))

