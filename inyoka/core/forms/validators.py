# -*- coding: utf-8 -*-
"""
    inyoka.core.forms.validators
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    our custom validators for the bureaucracy form system

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re
from urlparse import urlparse
from inyoka.i18n import lazy_gettext, _
from inyoka.core.forms import exceptions as exc


_mail_re = re.compile(r'''(?xi)
    (?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+
        (?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|
        "(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|
          \\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@.
''')


#XXX: according to rfc4622 a nodeid is optional. But we require one
#     'cause nobody should enter a service-jid in the jabber field.
#     Should we permit or deny? If we permit we need to validate the
#     domain and resid!
_jabber_re = re.compile(r'(?xi)(?:[a-z0-9!$\(\)*+,;=\[\\\]\^`{|}\-._~]+)@')



def check(validator, value, *args, **kwargs):
    """Call a validator and return True if it's valid, False otherwise.
    The first argument is the validator, the second a value.  All other
    arguments are forwarded to the validator function.

    >>> check(is_valid_email, 'foo@bar.com')
    True

    .. note::

        This function is for testing purposes only!
    """
    try:
        validator(*args, **kwargs)(None, value)
    except exc.ValidationError:
        return False
    return True


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
            raise exc.ValidationError(message)
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
            raise exc.ValidationError(message)
    return validator


def is_valid_jabber(message=None):
    if message is None:
        message = lazy_gettext(u'You have to enter a valid Jabber JID')
    def validator(form, value):
        if _jabber_re.match(value) is None:
            raise exc.ValidationError(message)
    return validator
