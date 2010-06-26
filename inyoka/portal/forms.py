# -*- coding: utf-8 -*-
"""
    inyoka.portal.forms
    ~~~~~~~~~~~~~~~~~~~

    Formulars for the portal.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.forms import Form, validators, widgets, BooleanField, TextField, \
    RecaptchaField
from inyoka.core.forms.utils import model_to_dict, update_model
from inyoka import Interface
from inyoka.core.database import db
from inyoka.i18n import _, lazy_gettext
from inyoka.core.auth.models import UserProfile, IUserProfileExtender


def get_profile_form():
    class ProfileForm(Form):
        def __init__(self, *args, **kwargs):
            self.profile = profile = kwargs.pop('profile')
            if profile is not None:
                profile_fields = IUserProfileExtender.get_profile_names()
                kwargs.update(model_to_dict(profile, fields=profile_fields))
            super(ProfileForm, self).__init__(*args, **kwargs)

        def save(self, commit=True):
            profile = UserProfile() if self.profile is None else self.profile
            profile_fields = IUserProfileExtender.get_profile_names()
            profile = update_model(profile, self, profile_fields)
            if commit:
                db.session.commit()
            return profile


    for name, field in IUserProfileExtender.get_profile_forms().iteritems():
        setattr(ProfileForm, name, field)

    return ProfileForm


class LoginForm(Form):
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
    captcha = RecaptchaField(lazy_gettext(u'ReCaptcha'))


class EditTagForm(Form):
    name = TextField(lazy_gettext(u'Name'), [validators.Length(max=20)])
