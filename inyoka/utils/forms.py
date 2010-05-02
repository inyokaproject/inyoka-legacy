# -*- coding: utf-8 -*-
"""
    inyoka.utils.forms
    ~~~~~~~~~~~~~~~~~~

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from urlparse import urlparse
from functools import partial
from wtforms import widgets
from wtforms.fields import Field
from wtforms.validators import ValidationError
from inyoka.i18n import get_translations, lazy_gettext
from inyoka.core.database import db
from inyoka.core.context import local, ctx
from inyoka.utils.datastructures import _missing



#class Form(FormBase):
#    """A somewhat extended base form to include our
#    i18n mechanisms as well as other things like sessions and such stuff.
#    """
#
#    # Until I resolved that redirect_tracking in bureaucracy
#    redirect_tracking = False
#
#    recaptcha_public_key = ctx.cfg['recaptcha.public_key']
#    recaptcha_private_key = ctx.cfg['recaptcha.private_key']
#
#    def _get_translations(self):
#        """Return our translations"""
#        return get_translations()
#
#    def _lookup_request_info(self):
#        """Return our current request object"""
#        if hasattr(local, 'request'):
#            return local.request
#
#    def _get_wsgi_environ(self):
#        """Return the WSGI environment from the request info if possible."""
#        request = self._lookup_request_info()
#        return request.environ if request is not None else None
#
#    def _get_request_url(self):
#        """The absolute url of the current request"""
#        request = self._lookup_request_info()
#        return request.current_url if request is not None else ''
#
#    def _redirect_to_url(self, url):
#        return redirect_(url)
#
#    def _resolve_url(self, args, kwargs):
#        assert len(args) == 1
#        return href(args[0], **kwargs)
#
#    def _get_session(self):
#        request = self._lookup_request_info()
#        return request.session if request is not None else {}
#
#    def _autodiscover_data(self):
#        request = self._lookup_request_info()
#        return request.form


class CommaSeperated(Field):
    widget = widgets.TextInput()

    def _value(self):
        if self.data:
            return u', '.join(self.data)
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [x.strip() for x in valuelist[0].split(',')]
        else:
            self.data = []


#class ModelField(Field):
#    """A field that queries for a model.
#
#    The first argument is the name of the model, the second the named
#    argument for `filter_by` (eg: `User` and ``'username'``).  If the
#    key is not given (None) the primary key is assumed.
#    """
#    messages = dict(not_found=lazy_gettext(u'“%(value)s” does not exist'))
#
#    def __init__(self, model, key=None, label=None, help_text=None,
#                 required=False, message=None, validators=None, widget=None,
#                 messages=None, on_not_found=None):
#        Field.__init__(self, label, help_text, validators, widget, messages)
#        self.model = model
#        self.key = key
#        self.required = required
#        self.message = message
#        self.on_not_found = on_not_found
#
#    def convert(self, value):
#        if isinstance(value, self.model):
#            return value
#        if not value:
#            if self.required:
#                raise exceptions.ValidationError(self.messages['required'])
#            return None
#
#        q = self.model.query.autoflush(False)
#
#        if self.key is None:
#            rv = q.get(value)
#        else:
#            rv = q.filter_by(**{self.key: value}).first()
#
#        if rv is None:
#            if self.on_not_found is not None:
#                return self.on_not_found(value)
#            else:
#                raise exceptions.ValidationError(self.messages['not_found'] %
#                                  {'value': value})
#        return rv
#
#    def to_primitive(self, value):
#        if value is None:
#            return u''
#        elif isinstance(value, self.model):
#            if self.key is None:
#                value = db.class_mapper(self.model) \
#                          .primary_key_from_instance(value)[0]
#            else:
#                value = getattr(value, self.key)
#        return unicode(value)
#
#
#class Autocomplete(CommaSeparated):
#    widget = TokenInput
#
#
#class BooleanField(BooleanField):
#    widget = widgets.FixedCheckbox


def _get_attrs(obj):
    not_underscore = partial(filter, lambda k: not k.startswith('_'))
    attrs = (attr.key for attr in type(obj)._sa_class_manager.attributes)
    return not_underscore(attrs)


def model_to_dict(instance, fields=None, exclude=None):
    """Returns a dict containing the data in ``instance`` suitable for passing as
    a Form's ``initial`` keyword argument.

    Example Usage::

        form = ContactForm(model_to_dict(user))

    :param fields: This is an optional list of field names.  If provided only
                   the named fields will be included in the returned dict.
    :param exclude:  This is an optional list of field names.  If provided
                     the named fields will be excluded from the returned dict.
    """
    data = {}

    for key in _get_attrs(instance):
        if fields and key not in fields:
            continue
        if exclude and key in exclude:
            continue

        data[key] = getattr(instance, key)
    return data


def update_model(instance, form, includes=None):
    """Update a model with the applied `form`.

    Example Usage::

        if request.method == 'POST' and form.validate():
            user = update_model(user, form)
            db.session.update(user)
            db.session.commit()

    If `includes` is applied only these fields will be updated.  This function
    fails silently if you applied the wrong include keys or tried to update
    not existing attributes.
    """
    attrs = _get_attrs(instance)
    if not isinstance(form, dict):
        # assume we work with a form instance instead of a dicct
        form = form.data.copy()

    for key, value in form.iteritems():
        if key not in attrs:
            continue
        if includes and key not in includes:
            continue

        setattr(instance, key, value)
    return instance


_mail_re = re.compile(r'''(?xi)
    (?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+
        (?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|
        "(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|
          \\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@.
''')


#NOTE: according to rfc4622 a nodeid is optional. But we require one
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


def is_valid_jabber(message=None):
    """Check if the string passed is a valid Jabber ID.

    This does neither check the domain nor the ressource id because we
    require an adress similar to a email adress with a nodeid set.

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
    def validator(form, value):
        if _jabber_re.match(value) is None:
            raise ValidationError(message)
    return validator

#
#from inyoka.core.models import Tag
#from inyoka.core.routing import href
#from inyoka.core.serializer import get_serializer, primitive
#
#
#class TokenInput(TextInput):
#    def render(self, **attrs):
#        input_html = super(TextInput, self).render(**attrs)
#        tags = self._form.data[self.name]
#        serializer, mime = get_serializer('json')
#        ro = primitive(tags, config={
#            'show_type': False,
#            Tag.object_type: ('id', 'name')
#        })
#        tags_json = serializer(ro)
#        js = """<script type="text/javascript">
#$(document).ready(function () {
#  $("#%s").tokenInput("%s", {'prePopulate': %s});
#});
#</script>""" % (self.id, href('api/core/get_tags', format='json'), tags_json)
#        return input_html + js
