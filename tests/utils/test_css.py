#-*- coding: utf-8 -*-
"""
    test_utils_css
    ~~~~~~~~~~~~~~

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.utils.css import filter_style


class TestCssUtils(TestCase):

    def test_unwanted_css_properties(self):
        """Test for some xss wholes."""
        self.assertEqual(filter_style(u'background-image: url(javascript: alert("foo"));'), u'')
        self.assertEqual(filter_style(u'-moz-binding: url("http://foobar.xy");'), u'')
        # this makes the ie corrupt and confusing…
        self.assertEqual(filter_style(u'width: expression((documentElement.clientWidth < 725) ? "725px" : "auto" )'), u'')
        # and this is also known to be a security risk in internet explorer
        self.assertEqual(filter_style(u'behavior: url("pngbehavior.htc");'), u'')

    def test_wanted_css_properties(self):
        self.assertEqual(filter_style(u'cursor: pointer; color: black;'), u'cursor: pointer; color: black')
        self.assertEqual(filter_style(u'background-color: black;'), u'background-color: black')
        self.assertEqual(filter_style(u'margin-bottom: 2px;'), u'margin-bottom: 2px')
        self.assertEqual(filter_style(u'padding-top: 5px;'), u'padding-top: 5px')

    def test_invalid_css_keyword(self):
        self.assertEqual(filter_style(u'padding-top: 5kg;'), u'')

    def test_css_none(self):
        self.assertEqual(filter_style(None), None)
