# -*- coding: utf-8 -*-
"""
    inyoka.utils.xml
    ~~~~~~~~~~~~~~~~

    This module implements XML-related functions and classes.

    This module is slightly ported from `Zine <http://zine.pocoo.org>`

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from htmlentitydefs import name2codepoint
from markupsafe import escape


_entities = {'\n': '&#10;', '\r': '&#13;', '\t': '&#9;'}
_entity_re = re.compile(r'&([^;]+);')
_striptags_re = re.compile(r'(<!--.*?-->|<[^>]*>)')

#: the xml namespace
XML_NS = 'http://www.w3.org/XML/1998/namespace'

#: a dict of html entities to codepoints. This includes the problematic
#: &apos; character.
html_entities = name2codepoint.copy()
html_entities['apos'] = 39
del name2codepoint


def quoteattr(data):
    """Escape and quote an attribute value."""
    data = escape(data)
    if '"' in data:
        if "'" in data:
            data = '"%s"' % data.replace('"', "&quot;")
        else:
            data = "'%s'" % data
    else:
        data = '"%s"' % data
    return data


def replace_entities(string):
    """Replace HTML entities in a string:

    >>> replace_entities('foo &amp; bar &raquo; foo')
    u'foo & bar \\xbb foo'
    """
    def handle_match(m):
        name = m.group(1)
        if name in html_entities:
            return unichr(html_entities[name])
        if name[:2] in ('#x', '#X'):
            try:
                return unichr(int(name[2:], 16))
            except ValueError:
                return u''
        elif name.startswith('#'):
            try:
                return unichr(int(name[1:]))
            except ValueError:
                return u''
        return u''
    return _entity_re.sub(handle_match, string)


def to_text(element):
    """Convert an element into text only information."""
    result = []

    def _to_text(element):
        result.append(element.text or u'')
        for child in element.iterchildren():
            _to_text(child)
        result.append(element.tail or u'')

    _to_text(element)
    return u''.join(result)


def strip_tags(s, normalize_whitespace=True):
    """Remove HTML tags in a text.  This also resolves entities."""
    s = _striptags_re.sub('', s)
    s = replace_entities(s)
    if normalize_whitespace:
        s = ' '.join(s.split())
    return s


class Namespace(object):
    """Attribute access to this class returns fully qualified names for the
    given URI.

    >>> ns = Namespace('http://inyokaproject.org/')
    >>> ns.foo
    u'{http://inyokaproject.org/}foo'
    """

    def __init__(self, uri):
        self._uri = unicode(uri)

    def __getattr__(self, name):
        return u'{%s}%s' % (self._uri, name)

    def __getitem__(self, name):
        # to be able to use tag names using dashes
        return getattr(self, name)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return self._uri
