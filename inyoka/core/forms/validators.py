# -*- coding: utf-8 -*-
"""
    inyoka.core.forms.validators
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Form library based on WTForms.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from urlparse import urlparse
from wtforms.validators import email, equal_to, ip_address, length, \
    number_range, optional, required, regexp, url, any_of, none_of, \
    ValidationError
from inyoka.i18n import lazy_gettext
from inyoka.context import ctx
from inyoka.core.auth.models import User
from inyoka.core.models import tag_re as _tag_re


_mail_re = re.compile(r'''(?xi)
    (?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+
        (?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|
        "(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|
          \\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@.
''')


#NOTE: according to rfc4622 a nodeid is optional. But we require one
#      'cause nobody should enter a service-jid in the jabber field.
#      Should we permit or deny? If we permit we need to validate the
#      domain and resid!
_jabber_re = re.compile(r'(?xi)(?:[a-z0-9!$\(\)*+,;=\[\\\]\^`{|}\-._~]+)@')


class DummyField(object):
    data = None


def check(validator, value, *args, **kwargs):
    """Call a validator and return True if it's valid, False otherwise.
    The first argument is the validator, the second a value.  All other
    arguments are forwarded to the validator function.

    >>> check(is_valid_email, 'foo@bar.com')
    True

    .. note::

        This function is for testing purposes only!
    """
    field = DummyField()
    field.data = value
    try:
        validator(*args, **kwargs)(None, field)
    except ValidationError:
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
        message = lazy_gettext(u'You have to enter a valid email address.')
    def validator(form, field):
        value = field.data
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
    def validator(form, field):
        protocol = urlparse(field.data)[0]
        if not protocol or protocol == 'javascript':
            raise ValidationError(message)
    return validator


def is_valid_jabber(message=None):
    """Check if the string passed is a valid Jabber ID.

    This does neither check the domain nor the ressource id because we
    require an address similar to a email address with a nodeid set.

    Since that nodeid is optional in the real-world we'd have to check
    the domain and ressource id if it's not specified.  To avoid that
    we require that nodeid.

    Examples::

        >>> check(is_valid_jabber, 'ente@quaki.org')
        True
        >>> check(is_valid_jabber, 'boy_you_suck@') # we don't check the domain
        True
        >>> check(is_valid_jabber, "yea, that's invalid")
        False
    """
    if message is None:
        message = lazy_gettext(u'You have to enter a valid Jabber ID')
    def validator(form, field):
        if _jabber_re.match(field.data) is None:
            raise ValidationError(message)
    return validator


def is_valid_recaptcha(message=None):
    """Check if the captcha was filled correctly."""
    if message is None:
        message = lazy_gettext(u'You entered an invalid captcha.')
    def validator(form, field):
        from inyoka.utils.captcha import validate_recaptcha
        req = ctx.current_request
        valid = validate_recaptcha(ctx.cfg['recaptcha.private_key'],
            req.form.get('recaptcha_challenge_field'),
            req.form.get('recaptcha_response_field'),
            req.environ['REMOTE_ADDR'] if req else None)

        if not valid:
            raise ValidationError(message)
    return validator


def is_user(message=None, key='username', negative=False):
    """
    Try to get an user either by name or by email (use the `key` parameter to
    specify this).
    Raises a validation error if no user was found. You can change this
    behaviour by setting `negative`.
    """
    if message is None:
        if key == 'username':
            message = negative and lazy_gettext(u'This user does already exist'
                             ) or lazy_gettext(u'This user doesn\'t exist')
        else:
            message = negative and lazy_gettext(u'This email address is already'
                  u' used') or lazy_gettext(u'There\'s no user with this email')

    def validator(form, field):
        user = User.query.filter_by(**{key: field.data}).first()
        if (negative and user) or (not negative and not user):
            raise ValidationError(message)

    return validator


def is_valid_attachment_name():
    def validator(form, field):
        if u'/' in field.data:
            raise ValidationError(lazy_gettext(u'The name must not contain '
                                               u'slashes.'))
    return validator


def is_valid_tag_name():
    def validator(form, field):
        if not _tag_re.match(field.data):
            raise ValidationError(lazy_gettext(u'Tag Names should only contain '
                                               u'ascii characters and numbers.'))
    return validator
