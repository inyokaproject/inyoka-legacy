# -*- coding: utf-8 -*-
"""
    inyoka.core.auth.forms
    ~~~~~~~~~~~~~~~~~~~~~~

    Forms for the Inyoka authentication framework.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core import forms
from inyoka.i18n import lazy_gettext

class StandardLoginForm(forms.Form):
    """Used to log in users."""
    username = forms.TextField(lazy_gettext(u'Username'), required=True)
    password = forms.TextField(lazy_gettext(u'Password'), required=True,
                               widget=forms.widgets.PasswordInput)
    permanent = forms.BooleanField(lazy_gettext(u'Permanent Login'))

    def __init__(self, auth_system, initial=None, action=None, request=None):
        forms.Form.__init__(self, initial, action, request)
        self.auth_system = auth_system
        if self.auth_system.passwordless:
            del self.fields['password']


class RegistrationForm(forms.Form):
    username = forms.TextField(lazy_gettext(u'Username'), required=True)
    email = forms.TextField(lazy_gettext(u'Email'), required=True)
    password = forms.TextField(lazy_gettext(u'Password'), required=True,
                               widget=forms.widgets.PasswordInput)
    password_again = forms.TextField(lazy_gettext(u'Password again'), required=True,
                               widget=forms.widgets.PasswordInput)

    def context_validate(self, data):
        if data['password'] != data['password_again']:
            raise forms.ValidationError(lazy_gettext(
                u'The two passwords must be the same'
            ))
