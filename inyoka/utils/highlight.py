# -*- coding: utf-8 -*-
"""
    inyoka.utils.highlight
    ~~~~~~~~~~~~~~~~~~~~~~

    Utils for highlighting code.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, \
    get_lexer_for_mimetype, TextLexer
from pygments.util import ClassNotFound

CLASSNAME = 'highlighted'

_default_formatter = HtmlFormatter(cssclass=CLASSNAME, linenos='table',
                                    lineanchors='cl', anchorlinenos=True)
_inline_formatter = HtmlFormatter(cssclass=CLASSNAME)


def highlight_code(code, lang=None, filename=None, mimetype=None, inline=False):
    """Highlight a block using pygments to HTML."""
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

    return highlight(code, lexer, _default_formatter if not inline else _inline_formatter)
