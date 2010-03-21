# -*- coding: utf-8 -*-
"""
    inyoka.core.forms
    ~~~~~~~~~~~~~~~~~

    This module uses `bureaucracy <http://dev.pocoo.org/hg/bureaucracy-main/>`_
    as it's base and stays here for API reasons.

    The :module:`inyoka.core.forms` module is a complete wrapper around bureaucracy
    and implements some features special for Inyoka.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from bureaucracy.forms import *
from bureaucracy import csrf, exceptions, recaptcha, redirects

from inyoka.i18n import get_translations, lazy_gettext
from inyoka.core.context import local, ctx
from inyoka.core.database import db
from inyoka.utils.datastructures import _missing


class Form(FormBase):
    """A somewhat extended base form to include our
    i18n mechanisms as well as other things like sessions and such stuff.
    """

    # Until I resolved that redirect_tracking in bureaucracy
    redirect_tracking = False

    recaptcha_public_key = ctx.cfg['recaptcha.public_key']
    recaptcha_private_key = ctx.cfg['recaptcha.private_key']

    def _get_translations(self):
        """Return our translations"""
        return get_translations()

    def _lookup_request_info(self):
        """Return our current request object"""
        if hasattr(local, 'request'):
            return local.request

    def _get_wsgi_environ(self):
        """Return the WSGI environment from the request info if possible."""
        request = self._lookup_request_info()
        return request.environ if request is not None else None

    def _get_request_url(self):
        """The absolute url of the current request"""
        request = self._lookup_request_info()
        return request.current_url if request is not None else ''

    def _redirect_to_url(self, url):
        return redirect_(url)

    def _resolve_url(self, args, kwargs):
        assert len(args) == 1 # TODO
        return href(args[0], **kwargs)

    def _get_session(self):
        request = self._lookup_request_info()
        return request.session if request is not None else {}

    def _autodiscover_data(self):
        request = self._lookup_request_info()
        return request.form


class ModelField(Field):
    """A field that queries for a model.

    The first argument is the name of the model, the second the named
    argument for `filter_by` (eg: `User` and ``'username'``).  If the
    key is not given (None) the primary key is assumed.
    """
    messages = dict(not_found=lazy_gettext(u'“%(value)s” does not exist'))

    def __init__(self, model, key=None, label=None, help_text=None,
                 required=False, message=None, validators=None, widget=None,
                 messages=None, on_not_found=None):
        Field.__init__(self, label, help_text, validators, widget, messages)
        self.model = model
        self.key = key
        self.required = required
        self.message = message
        self.on_not_found = on_not_found

    def convert(self, value):
        if isinstance(value, self.model):
            return value
        if not value:
            if self.required:
                raise exceptions.ValidationError(self.messages['required'])
            return None

        q = self.model.query.autoflush(False)

        if self.key is None:
            rv = q.get(value)
        else:
            rv = q.filter_by(**{self.key: value}).first()

        if rv is None:
            if self.on_not_found is not None:
                return self.on_not_found(value)
            else:
                raise exceptions.ValidationError(self.messages['not_found'] %
                                  {'value': value})
        return rv

    def to_primitive(self, value):
        if value is None:
            return u''
        elif isinstance(value, self.model):
            if self.key is None:
                value = db.class_mapper(self.model) \
                          .primary_key_from_instance(value)[0]
            else:
                value = getattr(value, self.key)
        return unicode(value)

class Autocomplete(CommaSeparated):
    from widgets import TokenInput
    widget = TokenInput
