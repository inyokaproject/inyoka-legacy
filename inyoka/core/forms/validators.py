#-*- coding: utf-8 -*-
"""
    inyoka.core.forms.validators
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    our custom validators for the bureaucracy form system

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re
from urlparse import urlparse

from inyoka.core.i18n import lazy_gettext, _
from inyoka.utils.text import _placeholder_re, _slug_parts


_mail_re = re.compile(r'''(?xi)
    (?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+
        (?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|
        "(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|
          \\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@.
''')

#TODO: this module is yet unused, because bureaucracy does not have
#      any validator api for now.
#
'''

def is_valid_email(message=None):
    """Check if the string passed is a valid mail address.

    >>> check(is_valid_email, 'somebody@example.com')
    True
    >>> check(is_valid_email, 'somebody AT example DOT com')
    False
    >>> check(is_valid_email, 'some random string')
    False

    Because e-mail validation is painfully complex we just check the first
    part of the email if it looks okay (comments are not handled!) and ignore
    the second.
    """
    if message is None:
        message = lazy_gettext(u'You have to enter a valid e-mail address.')
    def validator(form, value):
        if len(value) > 250 or _mail_re.match(value) is None:
            raise ValidationError(message)
    return validator


def is_valid_url(message=None):
    """Check if the string passed is a valid URL.  We also blacklist some
    url schemes like javascript for security reasons.

    >>> check(is_valid_url, 'http://pocoo.org/')
    True
    >>> check(is_valid_url, 'http://zine.pocoo.org/archive')
    True
    >>> check(is_valid_url, 'zine.pocoo.org/archive')
    False
    >>> check(is_valid_url, 'javascript:alert("Zine rocks!");')
    False
    """
    if message is None:
        message = lazy_gettext(u'You have to enter a valid URL.')
    def validator(form, value):
        protocol = urlparse(value)[0]
        if not protocol or protocol == 'javascript':
            raise ValidationError(message)
    return validator


def is_valid_slug(allow_slash=True):
    """Check if the value given is a valid slug:

    >>> check(is_valid_slug, '/foo')
    False
    >>> check(is_valid_slug, 'foo/bar')
    True
    """
    def validator(form, value):
        if len(value) > 200:
            raise ValidationError(_(u'The slug is too long'))
        elif value.startswith('/'):
            raise ValidationError(_(u'The slug must not start with a slash'))
    return validator
'''
