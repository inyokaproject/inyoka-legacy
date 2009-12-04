# -*- coding: utf-8 -*-
"""
    test_html
    ~~~~~~~~~

    tests for the inyoka html utilities

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.utils.html import escape


def test_quoted_escape():
    eq_(escape(u'My father said: "You rocks!"'),
        u'My father said: &quot;You rocks!&quot;')
    eq_(escape(u'My mother "sleeps"', quote=False),
        u'My mother "sleeps"')
