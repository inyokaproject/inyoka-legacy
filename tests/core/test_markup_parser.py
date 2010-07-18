# -*- coding: utf-8 -*-
"""
    test_wiki_parser
    ~~~~~~~~~~~~~~~~

    This unittests tests the parser.

    :copyright: 2010 by the Project Name Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from inyoka.core.markup.parser import Parser
from inyoka.core.markup import nodes


def parse(code):
    """
    Simple parsing function that doesn't use any transformers. This also
    prints the tree for easier debugging.
    """
    tree = Parser(code, transformers=[]).parse()
    return tree


def test_inline_formattings():
    """Simple test for some inline formattings."""
    tree = parse("''baz'' but '''foo''' and __bar__.")
    assert tree == nodes.Document([
        nodes.Emphasized([
            nodes.Text('baz')
        ]),
        nodes.Text(' but '),
        nodes.Strong([
            nodes.Text('foo')
        ]),
        nodes.Text(' and '),
        nodes.Underline([
            nodes.Text('bar')
        ]),
        nodes.Text('.')
    ])


def test_escaping():
    """Check if escaping works properly."""
    tree = parse("\\__bar\\__")
    assert tree == nodes.Document([
        nodes.Text("__bar__")
    ])

    tree = parse("'bar'")
    assert tree == nodes.Document([
        nodes.Text("'bar'")
    ])


def test_autoclosing():
    """Check if the automatic closing works."""
    tree = parse("''foo __bar")
    assert tree == nodes.Document([
        nodes.Emphasized([
            nodes.Text('foo '),
            nodes.Underline([
                nodes.Text('bar')
            ])
        ])
    ])


def test_simple_lists():
    """Check if simple lists work."""
    tree = parse(' * foo\n * ^^(bar)^^\n * ,,(baz),,')
    assert tree == nodes.Document([
        nodes.List('unordered', [
            nodes.ListItem([nodes.Text('foo')]),
            nodes.ListItem([
                nodes.Sup([nodes.Text('bar')])
            ]),
            nodes.ListItem([
                nodes.Sub([nodes.Text('baz')])
            ])
        ])
    ])


def test_nested_lists():
    """Check if nested lists work."""
    tree = parse(' * foo\n  1. bar\n   a. baz\n * blub')
    assert tree == nodes.Document([
        nodes.List('unordered', [
            nodes.ListItem([
                nodes.Text('foo'),
                nodes.List('arabic', [
                    nodes.ListItem([
                        nodes.Text('bar'),
                        nodes.List('alphalower', [
                            nodes.ListItem([nodes.Text('baz')])
                        ])
                    ])
                ])
            ]),
            nodes.ListItem([nodes.Text('blub')])
        ])
    ])


def test_simple_table():
    """Test the simple table markup."""
    tree = parse('||1||2||3||\n||4||5||6||')
    assert tree == nodes.Document([
        nodes.Table([
            nodes.TableRow([
                nodes.TableCell([nodes.Text('1')]),
                nodes.TableCell([nodes.Text('2')]),
                nodes.TableCell([nodes.Text('3')])
            ]),
            nodes.TableRow([
                nodes.TableCell([nodes.Text('4')]),
                nodes.TableCell([nodes.Text('5')]),
                nodes.TableCell([nodes.Text('6')])
            ])
        ])
    ])


def test_span_table():
    """Test tables with col/rowspans."""
    tree = parse('||<-2>1||<|2>2||\n||3||4||')
    assert tree == nodes.Document([
        nodes.Table([
            nodes.TableRow([
                nodes.TableCell([nodes.Text('1')], colspan=2),
                nodes.TableCell([nodes.Text('2')], rowspan=2)
            ]),
            nodes.TableRow([
                nodes.TableCell([nodes.Text('3')]),
                nodes.TableCell([nodes.Text('4')])
            ])
        ])
    ])


def test_table_row_classes():
    """Test the table row class assignments."""
    tree = parse('||<foo>1||2||3')
    assert tree == nodes.Document([
        nodes.Table([
            nodes.TableRow([
                nodes.TableCell([nodes.Text('1')]),
                nodes.TableCell([nodes.Text('2')]),
                nodes.TableCell([nodes.Text('3')])
            ], class_='foo')
        ])
    ])


def test_table_cell_classes():
    """Test the table cell classes."""
    tree = parse('||<cellclass=foo>1||<bar>2||')
    assert tree == nodes.Document([
        nodes.Table([
            nodes.TableRow([
                nodes.TableCell([nodes.Text('1')], class_='foo'),
                nodes.TableCell([nodes.Text('2')], class_='bar')
            ])
        ])
    ])


def test_table_alignment():
    """Check if table alignment parameters work."""
    tree = parse('||<:~>1||<(v>2||<)^>3||')
    assert tree == nodes.Document([
        nodes.Table([
            nodes.TableRow([
                nodes.TableCell([nodes.Text('1')], align='center', valign='middle'),
                nodes.TableCell([nodes.Text('2')], align='left', valign='bottom'),
                nodes.TableCell([nodes.Text('3')], align='right', valign='top')
            ])
        ])
    ])


def test_pre():
    """Test normal pre blocks."""
    tree = parse('{{{\nfoo\n}}}')
    assert tree == nodes.Document([
        nodes.Preformatted([nodes.Text('foo')])
    ])


def test_breakers():
    """Test the ruler."""
    tree = parse('foo\n-----------------')
    assert tree == nodes.Document([
        nodes.Text('foo\n'),
        nodes.Ruler()
    ])


def test_external_links():
    """Test all kind of external links."""
    tree = parse('[http://example.org :blub:][?action=edit]')
    assert tree == nodes.Document([
        nodes.Link('http://example.org', [nodes.Text(':blub:')]),
        nodes.Link('?action=edit')
    ])
