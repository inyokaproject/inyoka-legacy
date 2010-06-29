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
from inyoka.core.database import db
from inyoka.i18n import lazy_gettext
from inyoka.core.auth.models import UserProfile


class ProfileForm(Form):

    # personal data
    real_name = TextField(lazy_gettext(u'Realname'), [validators.Length(max=200)])
    website = TextField(lazy_gettext(u'Website'), validators=[validators.is_valid_url()])
    location = TextField(lazy_gettext(u'Location'), [validators.Length(max=200)])
    interests = TextField(lazy_gettext(u'Interests'), [validators.Length(max=200)])
    occupation = TextField(lazy_gettext(u'Occupation'), [validators.Length(max=200)])
    signature = TextField(lazy_gettext(u'Signature'), widget=widgets.TextArea())

    # communication channels
    jabber = TextField(lazy_gettext(u'Jabber ID'), validators=[validators.is_valid_jabber()])
    skype = TextField(lazy_gettext(u'Skype'), [validators.Length(max=200)])

    def __init__(self, *args, **kwargs):
        self.profile = profile = kwargs.pop('profile')
        if profile is not None:
            kwargs.update(model_to_dict(profile, exclude=['user', 'user_id']))
        super(ProfileForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        profile = UserProfile() if self.profile is None else self.profile
        profile = update_model(profile, self)
        if commit:
            db.session.commit()
        return profile


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
