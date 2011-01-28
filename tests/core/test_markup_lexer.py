# -*- coding: utf-8 -*-
"""
    test_markup_lexer
    ~~~~~~~~~~~~~~~~~

    This unittest tests various features of the wiki lexer. Just the lexer,
    not the parser.

    :copyright: 2010-2011 by the Project Name Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from inyoka.core.markup.lexer import Lexer


lexer = Lexer()


def test_inline_markup():
    expect = lexer.tokenize(
        u"''foo''"
        u"'''foo'''"
        u"__foo__"
        u',,(foo),,'
        u'^^(foo)^^'
        u'--(foo)--'
        u'`foo`'
        u'``foo``'
        u'~-(foo)-~'
        u'~+(foo)+~'
        u'((foo))'
        u'[mark]foo[/mark]'
        u'[raw]foo[/raw]'
        u'[color=red]foo[/color]'
        u'[size=10]foo[/size]'
        u'[font=Monaco]foo[/font]'
        u'[mod=foo]bar[/mod]'
        u'[edit=foo]bar[/edit]'
    ).expect

    for element in ('emphasized', 'strong', 'underline', 'sub', 'sup',
                    'stroke', 'code', 'escaped_code', 'small', 'big',
                    'footnote', 'highlighted'):
        expect(element + '_begin')
        expect('text', 'foo')
        expect(element + '_end')

    expect('raw', 'foo')

    expect('color_begin')
    expect('color_value', 'red')
    expect('text', 'foo')
    expect('color_end')
    expect('size_begin')
    expect('font_size', '10')
    expect('text', 'foo')
    expect('size_end')
    expect('font_begin')
    expect('font_face', 'Monaco')
    expect('text', 'foo')
    expect('font_end')
    expect('mod_begin')
    expect('username', 'foo')
    expect('text', 'bar')
    expect('mod_end')
    expect('edit_begin')
    expect('username', 'foo')
    expect('text')
    expect('edit_end')

    expect('eof')


def test_extra():
    expect = lexer.tokenize(
        u'--------------------\n'
        u'foo'
    ).expect

    expect('ruler')
    expect('text', 'foo')
    expect('eof')


def test_escape():
    expect = lexer.tokenize(
        u'\\__test\\__\\\\foo'
    ).expect

    expect('text', '__test__\\\\foo')
    expect('eof')


def test_links():
    expect = lexer.tokenize(
        u'[?action=edit]'
        u'[http://example.com example]'
    ).expect

    expect('external_link_begin')
    expect('link_target', '?action=edit')
    expect('external_link_end')

    expect('external_link_begin')
    expect('link_target', 'http://example.com')
    expect('text', 'example')
    expect('external_link_end')

    expect('eof')


def test_meta():
    expect = lexer.tokenize(
        u'## This is a comment\n'
        u'# This: is metadata'
    ).expect

    expect('metadata_begin')
    expect('metadata_key', 'This')
    expect('text', 'is metadata')
    expect('metadata_end')
    expect('eof')


def test_pre():
    expect = lexer.tokenize(
        u'{{{\nfoo\nbar\n}}}\n'
        u'{{{#!bar foo, blub=blah\nfoo\n}}}'
    ).expect

    expect('pre_begin')
    expect('text', '\nfoo\nbar\n')
    expect('pre_end')

    expect('text', '\n')

    expect('pre_begin')
    expect('parser_begin', 'bar')
    expect('text', 'foo')
    expect('func_argument_delimiter')
    expect('func_kwarg', 'blub')
    expect('text', 'blah')
    expect('parser_end')
    expect('text', '\nfoo\n')
    expect('pre_end')

    expect('eof')


def test_pre_quote_mixture():
    expect = lexer.tokenize('\n'.join((
        u'foo',
        u'{{{',
        u'> foo',
        u'}}}',
        u'bar'
    ))).expect
    expect('text', 'foo\n')
    expect('pre_begin')
    expect('text', '\n> foo\n')
    expect('pre_end')
    expect('text', '\nbar')
    expect('eof')


def test_table():
    expect = lexer.tokenize(
        u'||1||2||3||\n'
        u'||4||5||6||\n\n'
        u'||<42 foo=bar>1||'
    ).expect

    expect('table_row_begin')
    expect('text', '1')
    expect('table_col_switch')
    expect('text', '2')
    expect('table_col_switch')
    expect('text', '3')
    expect('table_row_end')

    expect('table_row_begin')
    expect('text', '4')
    expect('table_col_switch')
    expect('text', '5')
    expect('table_col_switch')
    expect('text', '6')
    expect('table_row_end')

    expect('text', '\n')

    expect('table_row_begin')
    expect('table_def_begin')
    expect('text', '42')
    expect('func_kwarg', 'foo')
    expect('text', 'bar')
    expect('table_def_end')
    expect('text', '1')
    expect('table_row_end')

    expect('eof')


def test_box():
    expect = lexer.tokenize(
        u'{{|\nfoo\n|}}\n'
        u'{{|<1 foo=2>\nfoo\n|}}'
    ).expect

    expect('box_begin')
    expect('text', '\nfoo\n')
    expect('box_end')

    expect('text', '\n')

    expect('box_begin')
    expect('box_def_begin')
    expect('text', '1')
    expect('func_kwarg', 'foo')
    expect('text', '2')
    expect('box_def_end')
    expect('text', '\nfoo\n')
    expect('box_end')

    expect('eof')


def test_list():
    expect = lexer.tokenize(
        ' * foo\n'
        '  * foo\n'
        ' 1. foo\n'
        ' a. foo'
    ).expect

    for x in xrange(4):
        expect('list_item_begin')
        expect('text', 'foo')
        expect('list_item_end')

    expect('eof')


def test_quote():
    expect = lexer.tokenize(
        '> foo\n'
        ">> '''bar\n"
        ">> bar'''\n"
        '> foo'
    ).expect

    expect('quote_begin')
    expect('text', 'foo')
    expect('quote_begin')
    expect('strong_begin')
    expect('text', 'bar\nbar')
    expect('strong_end')
    expect('quote_end')
    expect('text', 'foo')
    expect('quote_end')
    expect('eof')
