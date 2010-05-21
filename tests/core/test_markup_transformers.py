# -*- coding: utf-8 -*-
"""
    test_markup_transformers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Test our builtin transformers.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPl, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core.markup import nodes
from inyoka.core.markup.parser import render
from inyoka.core.markup.transformers import AutomaticParagraphs, HeadlineProcessor


def test_automatic_paragraphs_transformer():
    transformer = AutomaticParagraphs()
    tree = nodes.Document([nodes.Text('\nYea'), nodes.Strong([nodes.Text('foo')]),
        nodes.Text('\n\nfaz')])
    transformed = transformer.transform(tree)
    eq_(render(transformed, None, 'html'), '<p>\nYea<strong>foo</strong></p><p>faz</p>')

    # test paragraph with block tags
    tree = nodes.Document([nodes.Text('\nYea'), nodes.Ruler(), nodes.Text('\n\nfaz')])
    transformed = transformer.transform(tree)
    eq_(render(transformed, None, 'html'), '<p>\nYea</p><hr /><p>faz</p>')


def test_headline_processor_transformer():
    transformer = HeadlineProcessor()
    tree = nodes.Document([nodes.Headline(1, [nodes.Text('foo')], 'foo'),
        nodes.Paragraph([nodes.Text('some text')]), nodes.Headline(2, [nodes.Text('faz')], ''),
        nodes.Paragraph([nodes.Text('other text')]), nodes.Headline(1, [nodes.Text('foo')], 'foo')])

    expected = nodes.Document([nodes.Headline(1, [nodes.Text('foo')], 'foo'),
        nodes.Paragraph([nodes.Text('some text')]), nodes.Headline(2, [nodes.Text('faz')], 'empty-headline'),
        nodes.Paragraph([nodes.Text('other text')]), nodes.Headline(1, [nodes.Text('foo')], 'foo-2')])

    transformed = transformer.transform(tree)
    eq_(transformed, expected)
