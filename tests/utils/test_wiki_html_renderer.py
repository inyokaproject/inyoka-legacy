# -*- coding: utf-8 -*-
"""
    test_wiki_html_renderer
    ~~~~~~~~~~~~~~~~~~~~~~~

    Here we test the HTML rendering.

    :copyright: Copyright 2007 by Armin Ronacher.
    :license: GNU GPL.
"""
from inyoka.utils.parser import Parser, RenderContext


def render(source):
    """Parse source and render it to html."""
    tree = Parser(source, []).parse()
    html = tree.render(RenderContext(), 'html')
    return html


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
