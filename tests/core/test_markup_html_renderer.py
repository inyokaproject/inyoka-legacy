# -*- coding: utf-8 -*-
"""
    test_markup_html_renderer

    Here we test the HTML rendering.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core.markup.parser import Parser, RenderContext


def render(source):
    """Parse source and render it to html."""
    tree = Parser(source, []).parse()
    html = tree.render(RenderContext(), 'html')
    return html


def test_escaping():
    """Test html escaping"""
    eq_(render('<em>blub</em>'), u'&lt;em&gt;blub&lt;/em&gt;')
    eq_(render("you're so cool"), u"you&#39;re so cool")


def test_simple_markup():
    """Test the simple markup."""
    html = render("''foo'', '''bar''', __baz__, ,,(foo),,, ^^(bar)^^")
    assert html == (
        '<em>foo</em>, '
        '<strong>bar</strong>, '
        '<span class="underline">baz</span>, '
        '<sub>foo</sub>, '
        '<sup>bar</sup>'
    )


def test_pre():
    """Check if pre renders correctly."""
    assert render('{{{\n<em>blub</em>\n}}}') == (
        '<pre>&lt;em&gt;blub&lt;/em&gt;</pre>'
    )


def test_lists():
    """Check list rendering."""
    html = render(' * 1\n * 2\n  1. 3\n * 4')
    assert html == (
        '<ul>'
          '<li>1</li>'
          '<li>2<ol class="arabic">'
            '<li>3</li>'
          '</ol></li>'
          '<li>4</li>'
        '</ul>'
    )


def test_blockquotes():
    """Test block quote rendering."""
    html = render("> ''foo\n> bar''\n>> nested")
    assert html == (
        '<blockquote>'
          '<em>foo\nbar</em>'
          '<blockquote>nested</blockquote>'
        '</blockquote>'
    )
