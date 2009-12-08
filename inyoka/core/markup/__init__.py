# -*- coding: utf-8 -*-
"""
    inyoka.core.markup
    ~~~~~~~~~~~~~~~~~~

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.i18n import _
from inyoka.core.markup.lexer import Lexer
from inyoka.core.markup.machine import Renderer, RenderContext
from inyoka.core.markup.transformers import ITransformer
from inyoka.core.markup.constants import HTML_COLORS
from inyoka.core.markup import nodes
from unicodedata import lookup


__all__ = ['parse', 'render', 'stream', 'escape']


# the maximum depth of stack-protected nodes
MAXIMUM_DEPTH = 200


def parse(markup, wiki_force_existing=False, catch_stack_errors=True,
          transformers=None):
    """Parse markup into a node."""
    try:
        return Parser(markup, transformers, wiki_force_existing).parse()
    except StackExhaused:
        if not catch_stack_errors:
            raise
        return nodes.Paragraph([
            nodes.Strong([nodes.Text(_(u'Internal parser error: '))]),
            nodes.Text(_(u'The parser could not process the text because '
                         u'it exceeded the maximum allowed depth for nested '
                         u'elements'))
        ])


def render(instructions, context=None, format=None):
    """Render the compiled instructions."""
    if context is None:
        context = RenderContext()
    return Renderer(instructions).render(context, format)


def stream(instructions, context=None, format=None):
    """Stream the compiled instructions."""
    if context is None:
        context = RenderContext()
    return Renderer(instructions).stream(context, format)


def unescape_string(string):
    """
    Unescape a string with python semantics but silent fallback.
    """
    result = []
    write = result.append
    simple_escapes = {
        'a':    '\a',
        'n':    '\n',
        'r':    '\r',
        'f':    '\f',
        't':    '\t',
        'v':    '\v',
        '\\':   '\\',
        '"':    '"',
        "'":    "'",
        '0':    '\x00'
    }
    unicode_escapes = {
        'x':    2,
        'u':    4,
        'U':    8
    }
    chariter = iter(string)
    next_char = chariter.next

    try:
        for char in chariter:
            if char == '\\':
                char = next_char()
                if char in simple_escapes:
                    write(simple_escapes[char])
                elif char in unicode_escapes:
                    seq = [next_char() for x in xrange(unicode_escapes[char])]
                    try:
                        write(unichr(int(''.join(seq), 16)))
                    except ValueError:
                        pass
                elif char == 'N' and next_char() != '{':
                    seq = []
                    while True:
                        char = next_char()
                        if char == '}':
                            break
                        seq.append(char)
                    try:
                        write(lookup(u''.join(seq)))
                    except KeyError:
                        pass
                else:
                    write('\\' + char)
            else:
                write(char)
    except StopIteration:
        pass
    return u''.join(result)


class StackExhaused(ValueError):
    """
    Raised if the parser recognizes nested structures that would hit the
    stack limit.
    """


class Parser(object):
    """
    The wiki syntax parser.  Never use this class directly, always do this
    via the public `parse()` function of this module.  The behavior of this
    class in multithreaded environments is undefined (might change from
    revision to revision) and the `parse()` function knows how to handle that.
    Either be reusing parsers if safe, locking or reinstanciating.

    This parser should be considered a private class.  All of the attributes
    and methods exists for the internal parsing process.  As long as you don't
    extend the parser you should only use the `parse()` function (except of
    parser unittests which can savely user the `Parser` class itself).
    """

    def __init__(self, string, transformers=None, wiki_force_existing=False):
        """
        In theory you never have to instanciate this parser yourself because
        the high level `parse()` function encapsulates this.  However for the
        unittests it's important to be able to disable and enable the
        `transformers` by hand.  If you don't provide any transformers the
        default transformers are used.
        """
        self.string = string
        self.lexer = Lexer()
        self.stack_depth = 0
        if transformers is None:
            transformers = ITransformer.get_components()
        self.transformers = transformers
        self.wiki_force_existing = wiki_force_existing

        #: node dispatchers
        self._handlers = {
            'text':                 self.parse_text,
            'strong_begin':         self.parse_strong,
            'underline_begin':      self.parse_underline,
            'emphasized_begin':     self.parse_emphasized
        }

        #: runtime information
        self.is_dirty = False

    def parse_node(self, stream):
        """
        Call this with a `TokenStream` to dispatch to the correct parser call.
        If the current token on the stream is not handleable it will raise a
        `KeyError`.  However you should not relay on that behavior because the
        beavior is undefined and may change.  It's your reposibility to make
        sure the parser never calls `parse_node` on not existing nodes when
        extending the lexer / parser.
        """
        # stack exhausted, return a node that represents that
        if self.stack_depth >= MAXIMUM_DEPTH:
            raise StackExhaused()
        self.stack_depth += 1
        try:
            return self._handlers[stream.current.type](stream)
        finally:
            self.stack_depth -= 1

    def parse_text(self, stream):
        """Expects a ``'text'`` token and returns a `nodes.Text`."""
        return nodes.Text(stream.expect('text').value)

    def parse_underline(self, stream):
        """
        Parses the underline formatting.  This should really go away or change
        the meaning to *inserted* text in which situation this makes sense.

        Returns a `Underline` node.
        """
        stream.expect('underline_begin')
        children = []
        while stream.current.type != 'underline_end':
            children.append(self.parse_node(stream))
        stream.expect('underline_end')
        return nodes.Underline(children)

    def parse_strong(self, stream):
        """
        Parse strong emphasized text.

        Returns a `Strong` node.
        """
        stream.expect('strong_begin')
        children = []
        while stream.current.type != 'strong_end':
            children.append(self.parse_node(stream))
        stream.expect('strong_end')
        return nodes.Strong(children)

    def parse_emphasized(self, stream):
        """
        Parse normal emphasized text.

        Returns a `Emphasized` node.
        """
        stream.expect('emphasized_begin')
        children = []
        while stream.current.type != 'emphasized_end':
            children.append(self.parse_node(stream))
        stream.expect('emphasized_end')
        return nodes.Emphasized(children)

    def parse(self):
        """
        Starts the parsing process.  This sets the dirty flag which means that
        you have to create a new parser after the parsing.
        """
        if self.is_dirty:
            raise RuntimeError('the parser is dirty. reinstanciate it.')
        self.is_dirty = True
        stream = self.lexer.tokenize(self.string)
        result = nodes.Document()
        while not stream.eof:
            result.children.append(self.parse_node(stream))
        for transformer in self.transformers:
            result = transformer.transform(result)
        return result
