# -*- coding: utf-8 -*-
"""
    inyoka.utils.text
    ~~~~~~~~~~~~~~~~~

    Utilities for text processing

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
import unicodedata
from datetime import datetime
from itertools import starmap
from inyoka.i18n import rebase_to_timezone


_punctuation_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
_string_inc_re = re.compile(r'(\d+)$')
_placeholder_re = re.compile(r'%(\w+)%')


def gen_slug(text, delim=u'-', ascii=False):
    """Generates a proper slug for the given text.  It calls either
    `gen_ascii_slug` or `gen_unicode_slug` depending on the application
    configuration.
    """
    if ascii:
        return gen_ascii_slug(text, delim)
    return gen_unicode_slug(text, delim)


def gen_ascii_slug(text, delim=u'-'):
    """Generates an ASCII-only slug.
    """
    result = []
    for word in _punctuation_re.split(text.lower()):
        #TODO: transliterate `word` see :func:`transliterate` comment
        word = _punctuation_re.sub(u'', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))


def gen_unicode_slug(text, delim=u'-'):
    """Generate an unicode slug.
    """
    return unicode(delim.join(_punctuation_re.split(text.lower())))


def gen_timestamped_slug(slug, content_type, pub_date=None, prefix='',
                         fixed=False, url_format=None):
    """Generate a timestamped slug, suitable for use as final URL path."""
    if pub_date is None:
        pub_date = datetime.utcnow()
    pub_date = rebase_to_timezone(pub_date)

    if prefix:
        prefix = prefix.strip(u'/')
        prefix += u'/'

    if url_format is None:
        url_format = u'%year%/%month%/%day%/%slug%'

    if content_type == 'entry':
        def handle_match(match):
            name = match.group()
            handler = _slug_parts.get(match.group(1))
            if handler is None:
                return match.group(0)
            return handler(pub_date, slug, fixed)

        full_slug = prefix + _placeholder_re.sub(handle_match, url_format)
    else:
        full_slug = u'%s%s' % (prefix, slug)
    return full_slug


def increment_string(string):
    """Increment a string by one:

    >>> increment_string(u'test')
    u'test2'
    >>> increment_string(u'test2')
    u'test3'
    """
    match = _string_inc_re.search(string)
    if match is None:
        return string + u'2'
    return string[:match.start()] + unicode(int(match.group(1)) + 1)


def wrap(text, width):
    r"""A word-wrap function that preserves existing line breaks
    and most spaces in the text. Expects that existing line breaks are
    posix newlines (\n).
    """
    # code from http://code.activestate.com/recipes/148061/
    return reduce(lambda line, word, width=width: '%s%s%s' %
                  (line,
                   ' \n'[len(line) - line.rfind('\n') - 1 +
                         (word and len(word.split('\n', 1)[0]) or 0) >= width], word),
                   text.split(' '))


def _make_date_slug_part(key, places):
    def handler(datetime, slug, fixed):
        value = getattr(datetime, key)
        if fixed:
            return (u'%%0%dd' % places) % value
        return unicode(value)
    return key, handler


#: a dict of slug part handlers for gen_timestamped_slug
_slug_parts = dict(starmap(_make_date_slug_part, [
    ('year', 4),
    ('month', 2),
    ('day', 2),
    ('hour', 2),
    ('minute', 2),
    ('second', 2)
]))
_slug_parts['slug'] = lambda d, slug, f: slug
