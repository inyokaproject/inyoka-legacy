# -*- coding: utf-8 -*-
"""
    inyoka.utils.text
    ~~~~~~~~~~~~~~~~~

    Utilities for text processing.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
import random
import translitcodec
from datetime import datetime
from itertools import starmap


_punctuation_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
_string_inc_re = re.compile(r'(\d+)$')
_placeholder_re = re.compile(r'%(\w+)%')
_default_slug_format = u'%year%/%month%/%day%/%slug%'


def get_random_password():
    """This function returns a pronounceable word."""
    consonants = u'bcdfghjklmnprstvwz'
    vowels = u'aeiou'
    numbers = u'0123456789'
    all = consonants + vowels + numbers
    length = random.randrange(8, 12)
    password = u''.join(
        random.choice(consonants) +
        random.choice(vowels) +
        random.choice(all) for x in xrange(length // 3)
    )[:length]
    return password


def gen_slug(text, delim=u'-', ascii=False):
    """Generates a proper slug for the given text.

    It calls either :func:`gen_ascii_slug` or :func:`gen_unicode_slug`
    depending on the application configuration.

    .. note:: The slug is always lowercased and transliterated with
              translit/long codec.
    """
    if ascii:
        return gen_ascii_slug(text, delim)
    return gen_unicode_slug(text, delim)


def gen_ascii_slug(text, delim=u'-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _punctuation_re.split(text.lower()):
        word = _punctuation_re.sub(u'', word).encode('translit/long')
        if word:
            result.append(word)
    return unicode(delim.join(result))


def gen_unicode_slug(text, delim=u'-'):
    """Generate an unicode slug."""
    return unicode(delim.join(_punctuation_re.split(text.lower())))


def gen_timestamped_slug(slug, content_type, pub_date=None, prefix=u'',
                         fixed=False, url_format=_default_slug_format):
    """Generate a timestamped slug, suitable for use as final URL path.

    .. note:: `pub_date` will never be touched, neither localized nor converted
              to any timezone.
    """
    if pub_date is None:
        pub_date = datetime.utcnow()

    if prefix:
        prefix = prefix.strip(u'/')
        prefix += u'/'

    if content_type == 'entry':
        def handle_match(match):
            handler = _slug_parts.get(match.group(1))
            if handler is None:
                return match.group(0)
            return handler(pub_date, slug, fixed)

        full_slug = prefix + _placeholder_re.sub(handle_match, url_format)
    else:
        full_slug = u'%s%s' % (prefix, slug)
    return full_slug


def increment_string(string):
    """Increment a string by one

    Usage Example::

        >>> increment_string(u'test')
        u'test2'
        >>> increment_string(u'test2')
        u'test3'

    """
    match = _string_inc_re.search(string)
    if match is None:
        return string + u'2'
    return string[:match.start()] + unicode(int(match.group(1)) + 1)


def get_next_increment(values, string, max_length=None):
    """Return the next usable incremented string.

    Usage Example::

        >>> get_next_increment(['cat', 'cat10', 'cat2'], 'cat')
        u'cat11'
        >>> get_next_increment(['cat', 'cat2'], 'cat')
        u'cat3'
        >>> get_next_increment(['cat', 'cat1'], 'cat')
        u'cat2'
        >>> get_next_increment([], 'cat')
        'cat'
        >>> get_next_increment(['cat'], 'cat')
        u'cat2'
        >>> get_next_increment(['cat', 'cat10', 'cat2'], 'cat', 3)
        u'c11'
        >>> get_next_increment(['cat', 'cat100'], 'cat', 3)
        u'101'

    """
    values = list(values)
    if not values:
        return string

    base = None
    for value in values:
        match = _string_inc_re.search(value)
        if match is not None and int(match.group(1)) > base:
            base = int(match.group(1))

    gs = (lambda s: s if base is None else s + unicode(base))
    poi = increment_string(gs(string))
    if max_length is None:
        return poi

    if len(poi) > max_length:
        # we need to shorten the string a bit so that we don't break any rules
        strip = max_length - len(poi)
        string = string[:strip]
    return increment_string(gs(string))


def wrap(text, width):
    r"""A word-wrap function that preserves existing line breaks
    and most spaces in the text. Expects that existing line breaks are
    posix newlines (\n).
    """
    # code based on http://code.activestate.com/recipes/148061/
    def _wrap_text(line, word, width=width):
        breaks = (u' \n'[len(line) - line.rfind('\n') - 1 +
                  (word and len(word.split('\n', 1)[0]) or 0) >= width])
        return '%s%s%s' % (line, breaks, word)

    return reduce(_wrap_text, text.split(' '))


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
