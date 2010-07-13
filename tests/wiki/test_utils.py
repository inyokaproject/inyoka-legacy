# -*- coding: utf-8 -*-
"""
    test_utils
    ~~~~~~~~~~

    Unittests for the wiki.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug.exceptions import _ProxyException
from inyoka.core.api import href
from inyoka.core.exceptions import NotFound
from inyoka.core.test import *
from inyoka.core.auth.models import User
from inyoka.wiki.models import Page, Revision
from inyoka.wiki.utils import find_page


def _find_page_test_exception(url, *args, **kwargs):
    try:
        find_page(*args, **kwargs)
    except _ProxyException as err:
        r = err.get_response(None)
        assert r.status_code in (302, 303, 307)
        eq_(r.headers['Location'], url)
    else:
        raise ValueError('Should have raised redirect to %r' % url)


def test_find_page():
    u = User.query.first()
    p = Page.create(u'test page', change_user=u, text=u'foo')

    eq_(find_page('test_page', 'wiki/show', {}), p)
    eq_(find_page('test_page', 'wiki/show'), p)
    eq_(find_page('test_page', redirect=False), p)
    _find_page_test_exception(href('wiki/show', page='test_page'),
        'test page', 'wiki/show')
    _find_page_test_exception(href('wiki/show', page='test_page'),
        'test page', 'wiki/show', {})
    _find_page_test_exception(href('wiki/show', page='test_page', revision=1),
        'tEsT pAgE', 'wiki/show', {'revision': 1})
    assert_raises(NotFound, find_page, 'some inexistent page', 'wiki/show')
    assert_raises(NotFound, find_page, 'test page', redirect=False)

    db.session.delete(p.current_revision)
    db.session.delete(p)
    db.session.commit()
