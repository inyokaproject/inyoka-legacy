# -*- coding: utf-8 -*-
"""
    test_urls

    Unittests for the urls utilties.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core.api import href


def test_href():
    # set base domain name for correct testing
    domain = ctx.cfg['base_domain_name']
    eq_(href('portal/index'), '/')
    eq_(href('portal/index', _external=True), 'http://%s/' % domain)
    eq_(href('portal/index', _anchor='News'), '/#News')
    eq_(href('portal/index', _external=True, _anchor='News'), 'http://%s/#News' % domain)

    class HrefTester():
        def get_url_values(self, kw):
            if kw == 'foo':
                return 'portal/index', {'kw':'foo', '_anchor':'heydiho'}
            elif kw == 'bar':
                return 'portal/index', {'foo':'bar'}
    ht = HrefTester()
    eq_(href(ht, kw='foo'), '/?kw=foo#heydiho')
    eq_(href(ht, kw='foo', _anchor='bar'), '/?kw=foo#heydiho')
    eq_(href(ht, kw='bar'), '/?foo=bar')
