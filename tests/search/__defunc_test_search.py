# -*- coding: utf-8 -*-
"""
    test_search
    ~~~~~~~~~~~

    This module tests the queryparser and the indexer.

    :copyright: Copyright 2007 by Christoph Hack.
    :license: GNU GPL.
"""
from inyoka.utils.search import search, stem
from xapian import Query


def test_queryparser():
    qry_str = '(foo bar OR blub AND NOT test) OR (title:"example thread")'
    qry_parsed = search.parse_query(qry_str)
    qry = Query(Query.OP_OR,
                Query(Query.OP_AND,
                      Query(stem('foo'), 1, 1),
                      Query(Query.OP_OR,
                            Query(stem('bar'), 1, 2),
                            Query(Query.OP_AND_NOT,
                                  Query(stem('blub'), 1, 3),
                                  Query(stem('test'), 1, 4)))),
                Query(Query.OP_AND,
                      Query('T%s' % stem('example')),
                      Query('T%s' % stem('thread'))))
    assert qry_parsed.get_description() == qry.get_description()


def test_indexer_wiki():
    doc = search.create_document('wiki')
    doc['title'] = u'Here is the title'
    doc['text'] = u'This is only an example.'
    doc['area'] = 'Wiki'
    terms = set(term.term for term in doc._doc.termlist())
    assert terms == set(['her', 'this', 'titl', 'is', 'Tis',
                         'Awiki', 'Tthe', 'only', 'exampl', 'the',
                         'an', 'Ttitl', 'Ther'])
