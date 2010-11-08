#-*- coding: utf-8 -*-
"""
    test_utils_css
    ~~~~~~~~~~~~~~

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.utils.css import filter_style


#TODO: add more security problems here!

def test_unwanted_css_properties():
    """Test for some xss wholes."""
    assert filter_style(u'background-image: url(javascript: alert("foo"));') == u''
    assert filter_style(u'-moz-binding: url("http://foobar.xy");') == u''
    # this makes the ie corrupt and confusing…
    assert filter_style(u'width: expression((documentElement.clientWidth < 725) ? "725px" : "auto" )') == u''
    # and this is also known to be a security risk in internet explorer
    assert filter_style(u'behavior: url("pngbehavior.htc");') == u''
