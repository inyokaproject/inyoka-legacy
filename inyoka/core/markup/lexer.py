# -*- coding: utf-8 -*-
"""
    inyoka.core.markup.lexer
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Tokenizes our wiki markup.  The lexer is implemented as some sort of
    scanner with an internal stack.  Inspired by pygments.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from itertools import izip
from inyoka.utils.datastructures import TokenStream


def escape(text):
    """Escape a text with wiki formatting."""
    return Lexer().escape(text)


def bygroups(*args):
    """
    Callback creator for bygroup yielding.
    """
    return lambda m: izip(args, m.groups())


def astuple(token):
    """
    Yield the groups together as one tuple.
    """
    def wrapped(match):
        yield token, match.groups()
    return wrapped


def fallback():
    """
    Just pop and do nothing.
    """
    return rule('', leave=1)


def switch(state):
    """
    Go to another state when reached.
    """
    return rule('', switch=state)


class ruleset(tuple):
    """
    Rulesets keep some rules.  If at the end of parsing a ruleset is left
    on the stack a `name_end` token is emitted without a value.  If you don't
    want this behavior use the `helperset`.
    """
    __slots__ = ()

    def __new__(cls, *args):
        return tuple.__new__(cls, args)


class include(str):
    """
    Tells the lexer to include tokens from another set.
    """
    __slots__ = ()


class rule(object):
    """
    This represents a parsing rule.
    """
    __slots__ = ('match', 'token', 'enter', 'silententer', 'switch', 'leave')

    def __init__(self, regexp, token=None, enter=None, silententer=None,
                 switch=None, leave=0):
        self.match = re.compile(regexp, re.U).match
        self.token = token
        self.enter = enter
        self.silententer = silententer
        self.switch = switch
        self.leave = leave


class Lexer(object):

    rules = {
        'everything': ruleset(
            include('inline'),
        ),
        'inline': ruleset(
            rule('<!--.*?-->(?s)', None),
            rule("'''", enter='strong'),
            rule("''", enter='emphasized'),
            rule('__', enter='underline'),
        ),
        'strong': ruleset(
            rule("'''", leave=1),
            include('inline')
        ),
        'emphasized': ruleset(
            rule("''", leave=1),
            include('inline')
        ),
        'underline': ruleset(
            rule('__', leave=1),
            include('inline')
        ),
    }

    def tokenize(self, string):
        """
        Resolve quotes and parse quote for quote in an isolated environment.
        """
        buffer = []

        def tokenize_buffer():
            for item in self.tokenize_block(u'\n'.join(buffer)):
                yield item
            del buffer[:]

        def tokenize_blocks():
            for line in string.splitlines():
                buffer.append(line)

            for item in tokenize_buffer():
                yield item

        return TokenStream.from_tuple_iter(tokenize_blocks())

    def tokenize_block(self, string, _escape_hint=None):
        escaped = False
        pos = 0
        end = len(string)
        stack = [(None, 'everything')]
        rule_cache = {}
        text_buffer = []
        add_text = text_buffer.append
        flatten = u''.join

        def iter_rules(x):
            for rule in self.rules[x]:
                if rule.__class__ is include:
                    for item in iter_rules(rule):
                        yield item
                else:
                    yield rule

        while pos < end:
            state = stack[-1][1]
            if state not in rule_cache:
                rule_cache[state] = list(iter_rules(state))
            for rule in rule_cache[state]:
                m = rule.match(string, pos)
                if m is not None:
                    # if the token is escaped we push the lexed
                    # value to the text buffer and ignore
                    if escaped or _escape_hint is not None:
                        add_text(m.group())
                        pos = m.end()
                        if _escape_hint is not None:
                            _escape_hint.append(m.start())
                        escaped = False
                        break

                    # first flush text that is left in the buffer
                    if text_buffer:
                        text = flatten(text_buffer)
                        if text:
                            yield 'text', text
                        del text_buffer[:]

                    # now enter the new scopes if entered in a
                    # non silent way
                    if rule.enter is not None:
                        stack.append((rule.enter + '_end', rule.enter))
                        yield rule.enter + '_begin', m.group()
                    elif rule.silententer is not None:
                        stack.append((None, rule.silententer))

                    # now process the data
                    if callable(rule.token):
                        for item in rule.token(m):
                            yield item
                    elif rule.token is not None:
                        yield rule.token, m.group()

                    # now check if we leave something. if the state was
                    # entered non silent, send a close token.
                    pos = m.end()
                    for x in xrange(rule.leave):
                        announce, item = stack.pop()
                        if announce is not None:
                            yield announce, m.group()

                    # switch to another state, postponing the nonsilent token
                    if rule.switch:
                        announce, item = stack.pop()
                        if announce is not None:
                            stack.append((announce, rule.switch))
                    break
            else:
                char = string[pos]
                if char == '\\':
                    if escaped:
                        # this is a fix for the problem that two backslashes
                        # inside are displayed as one, even in code blocks
                        if string[pos - 1] == '\\':
                            char = '\\\\'
                        else:
                            char = ''
                        escaped = False
                    else:
                        escaped = True
                        char = ''
                else:
                    if escaped:
                        char = '\\' + char
                    escaped = False
                add_text(char)
                pos += 1

        # if there is a bogus escaped push a backslash
        if escaped:
            add_text('\\')

        # if the text buffer is left filled, we flush it
        if text_buffer:
            text = flatten(text_buffer)
            if text:
                yield 'text', text

        # if there are things in the stack left we should
        # emit the end tokens
        for announce, item in reversed(stack):
            if announce is not None:
                yield announce, u''

    def escape(self, text):
        """Escape a text."""
        escapes = []
        gen = self.tokenize_block(u'\n'.join(text.splitlines()), escapes)
        text = u''.join(x[1] for x in gen)
        offset = 0
        for pos in escapes:
            pos = pos + offset
            text = text[:pos] + '\\' + text[pos:]
            offset += 1
        return text
