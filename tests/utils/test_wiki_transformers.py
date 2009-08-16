# -*- coding: utf-8 -*-
"""
    test_wiki_transformers
    ~~~~~~~~~~~~~~~~~~~~~~

    This module tests the wiki ast transformers.

    :copyright: Copyright 2007 by Armin Ronacher.
    :license: GNU GPL.
"""
from inyoka.utils.parser import Parser, nodes
from inyoka.utils.parser.transformers import AutomaticParagraphs, \
     GermanTypography, SmileyInjector, FootnoteSupport, HeadlineProcessor, \
     AutomaticStructure


def parse(source, transformer):
    """
    Helper function that parses sourcecode with one transformer. Additionally
    it prints the tree so that it appears in the debug output.
    """
    tree = Parser(source, [transformer]).parse()
    return tree


def test_automatic_paragraphs():
    """Test the automatic paragraph insertion."""
    tree = parse("foo\n\nbar ''baz''blub.\n * foo\n{{{\nfoo\n}}}\n\nblub",
                 AutomaticParagraphs())
    assert tree == nodes.Document([
        nodes.Paragraph([nodes.Text('foo')]),
        nodes.Paragraph([
            nodes.Text('bar '),
            nodes.Emphasized([
                nodes.Text('baz')
            ]),
            nodes.Text('blub.\n')
        ]),
        nodes.List('unordered', [
            nodes.ListItem([nodes.Paragraph([nodes.Text('foo')])])
        ]),
        nodes.Preformatted([
            nodes.Text('foo')
        ]),
        nodes.Paragraph([
            nodes.Text('blub')
        ])
    ])


def test_german_typography():
    """Test the German typography transformer."""
    tree = parse('"Hello World!". foo --- bar, foo -- bar', GermanTypography())
    assert tree == nodes.Document([
        nodes.Text(u'\u201eHello World!\u201c. foo \u2014 bar, foo \u2013 bar')
    ])


def test_smiley_injector():
    """
    Check the insertion capabilities of the SmileyInjector, not the
    database access of it. That's part of the wiki storage testsuite.
    """
    tree = parse(u"""Inline:-)is not allowed. ÖÄÜ This should work :-D. This too :-). Two smileys :-):-) should work too.
:-D And yet another XDline XDXD. :-)""",
                 SmileyInjector({
        ':-)':      'happy.png',
        ':-D':      'grin.png',
        'XD':       'xd.png',
    }))

    assert tree == nodes.Document([
        nodes.Text(u'Inline:-)is not allowed. ÖÄÜ This should work '),
        nodes.Image('grin.png', ':-D'), nodes.Text('. This too '),
        nodes.Image('happy.png', ':-)'), nodes.Text('. Two smileys '),
        nodes.Image('happy.png', ':-)'), nodes.Image('happy.png', ':-)'),
        nodes.Text(' should work too.\n'), nodes.Image('grin.png', ':-D'),
        nodes.Text(' And yet another XDline '),
        nodes.Image('xd.png', 'XD'), nodes.Image('xd.png', 'XD'),
        nodes.Text('. '), nodes.Image('happy.png', ':-)')
    ])


def test_footnote_support():
    """Check if the footnote support works flawlessly."""
    tree = parse('foo((bar)). bar((baz))', FootnoteSupport())
    assert tree == nodes.Document([
        nodes.Text('foo'),
        nodes.Footnote([nodes.Text('bar')], id=1),
        nodes.Text('. bar'),
        nodes.Footnote([nodes.Text('baz')], id=2),
        nodes.List('unordered', class_='footnotes', children=[
            nodes.ListItem([
                nodes.Link('#bfn-1', [nodes.Text('1')], id='fn-1'),
                nodes.Text(': '),   # this is intended behavior
                nodes.Text('bar')
            ]),
            nodes.ListItem([
                nodes.Link('#bfn-2', [nodes.Text('2')], id='fn-2'),
                nodes.Text(': '),   # this is intended behavior
                nodes.Text('baz')
            ])
        ])
    ])


def test_headline_processor():
    """Test the headline processing."""
    tree = parse('= foo =\n== foo ==\n== foo-2 ==', HeadlineProcessor())
    assert tree == nodes.Document([
        nodes.Headline(1, [nodes.Text('foo')], id='foo'),
        nodes.Text('\n'),
        nodes.Headline(2, [nodes.Text('foo')], id='foo-2'),
        nodes.Text('\n'),
        nodes.Headline(2, [nodes.Text('foo-2')], id='foo-2-2')
    ])


def test_automatic_structure():
    """Test the automatic structures."""
    tree = parse('= foo =\nfoobar\n== bar ==\nblub', AutomaticStructure())
    # XXX: is this really the expected output? I expected either nested sections
    # and no section depths, or section depts and no nesting.
    assert tree == nodes.Document([
        nodes.Section(1, [
            nodes.Headline(1, [nodes.Text('foo')]),
            nodes.Text('\nfoobar\n'),
            nodes.Section(2, [
                nodes.Headline(2, [nodes.Text('bar')]),
                nodes.Text('\nblub')
            ])
        ])
    ])
