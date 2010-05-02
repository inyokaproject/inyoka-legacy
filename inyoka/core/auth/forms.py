# -*- coding: utf-8 -*-
"""
    inyoka.core.auth.forms
    ~~~~~~~~~~~~~~~~~~~~~~

    Forms for the Inyoka authentication framework.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from wtforms import Form, BooleanField, TextField, validators, widgets
from inyoka.i18n import lazy_gettext


class StandardLoginForm(Form):
    """Used to log in users."""
    username = TextField(lazy_gettext(u'Username'), [validators.Required()])
    password = TextField(lazy_gettext(u'Password'), [validators.Required()],
                         widget=widgets.PasswordInput())
    permanent = BooleanField(lazy_gettext(u'Remember me'))

    def __init__(self, auth_system, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.auth_system = auth_system
        if self.auth_system.passwordless:
            del self.password


class RegistrationForm(Form):

    username = TextField(lazy_gettext(u'Username'), [validators.Required()])
    email = TextField(lazy_gettext(u'Email'), [validators.Required()])
    password = TextField(lazy_gettext(u'Password'), [validators.Required(),
        validators.EqualTo('confirm', message=lazy_gettext(u'Passwords must match'))],
        widget=widgets.PasswordInput())
    confirm = TextField(lazy_gettext(u'Repeat Passord'),
        [validators.Required()], widget=widgets.PasswordInput())
