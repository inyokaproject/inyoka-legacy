# -*- coding: utf-8 -*-
"""
    test_html
    ~~~~~~~~~

    tests for the inyoka html utilities

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.utils.html import build_html_tag


class TestHtmlUtilities(TestCase):

    def test_build_html_tag(self):
        self.assertEqual(build_html_tag('a'), u'<a>')
        self.assertEqual(build_html_tag('a', href='http://example.com'),
                         u'<a href="http://example.com">')
        self.assertEqual(build_html_tag('a', class_='stunning', href='http://abc.xy'),
                               u'<a href="http://abc.xy" class="stunning">')
        self.assertEqual(build_html_tag('a', classes=('stunning', 'awesome'),
                                        href='http://abc.xy'),
                         u'<a href="http://abc.xy" class="stunning awesome">')
        # test for empty tags
        self.assertEqual(build_html_tag('br'), u'<br>')
