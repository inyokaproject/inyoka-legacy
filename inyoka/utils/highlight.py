#-*- coding: utf-8 -*-
"""
    inyoka.utils.highlighting
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Utils for highlighting code.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, \
    get_lexer_for_mimetype, TextLexer
from pygments.util import ClassNotFound

_pygments_formatter = HtmlFormatter(style='colorful', cssclass='syntax',
                                    linenos='table')


def highlight_code(code, lang=None, filename=None, mimetype=None):
    """Highlight a block using pygments to HTML."""
    print 'highlighting %r with %s' % (code[:60], lang)
    try:
        lexer = None
        guessers = [(lang, get_lexer_by_name),
            (filename, get_lexer_for_filename),
            (mimetype, get_lexer_for_mimetype)
        ]
        for var, guesser in guessers:
            if var is not None:
                try:
                    lexer = guesser(var, stripnl=True, startinline=True)
                    break
                except ClassNotFound:
                    continue

        if lexer is None:
            lexer = TextLexer(stripnl=False)
    except LookupError:
        lexer = TextLexer(stripnl=False)
    return highlight(code, lexer, _pygments_formatter)
