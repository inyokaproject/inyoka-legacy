# -*- coding: utf-8 -*-
"""
    inyoka.portal.forms
    ~~~~~~~~~~~~~~~~~~~

    Formulars for the portal.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.forms import Form, validators, widgets, BooleanField, TextField, \
    RecaptchaField, PasswordField, IntegerField, MagicFilterForm
from inyoka.core.forms.fields import AutocompleteField, DatePeriodField
from inyoka.core.forms.utils import model_to_dict, update_model
from inyoka.core.database import db
from inyoka.core.models import Tag
from inyoka.i18n import lazy_gettext
from inyoka.core.auth.models import UserProfile
from inyoka.utils.text import get_random_password


class ProfileForm(Form):

    # personal data
    real_name = TextField(lazy_gettext(u'Realname'), [validators.length(max=200)])
    website = TextField(lazy_gettext(u'Website'),
        validators=[validators.optional(), validators.is_valid_url()])
    location = TextField(lazy_gettext(u'Location'), [validators.length(max=200)])
    interests = TextField(lazy_gettext(u'Interests'), [validators.length(max=200)])
    occupation = TextField(lazy_gettext(u'Occupation'), [validators.length(max=200)])
    signature = TextField(lazy_gettext(u'Signature'), widget=widgets.TextArea())

    # communication channels
    jabber = TextField(lazy_gettext(u'Jabber ID'),
        validators=[validators.optional(), validators.is_valid_jabber()])
    skype = TextField(lazy_gettext(u'Skype'), [validators.length(max=200)])

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
    username = TextField(lazy_gettext(u'Username'), [validators.required()])
    password = TextField(lazy_gettext(u'Password'), [validators.required()],
                         widget=widgets.PasswordInput())
    permanent = BooleanField(lazy_gettext(u'Remember me'))

    def __init__(self, auth_system, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.auth_system = auth_system
        if self.auth_system.passwordless:
            del self.password


def get_registration_form(request):
    random_pw = get_random_password() if 'random' in request.args else None

    class RegistrationForm(Form):
        username = TextField(lazy_gettext(u'Username'), [validators.required(),
            validators.is_user(negative=True)])
        email = TextField(lazy_gettext(u'Email'), [validators.required(),
            validators.is_user(negative=True, key='email')])
        password = PasswordField(lazy_gettext(u'Password'), [validators.required(),
            validators.equal_to('confirm', message=lazy_gettext(u'Passwords must match'))],
            widget=widgets.PasswordInput(False), default=random_pw)
        confirm = PasswordField(lazy_gettext(u'Repeat Passord'),
            [validators.required()], widget=widgets.PasswordInput(False),
            default=random_pw)
        captcha = RecaptchaField(lazy_gettext(u'ReCaptcha'))

    return RegistrationForm


class EditTagForm(Form):
    name = TextField(lazy_gettext(u'Name'), [validators.required(),
                validators.length(max=20),validators.is_valid_tag_name()])


class SearchForm(MagicFilterForm):
    csrf_disabled = True
    dynamic_fields = ['author', 'tags', 'date']

    q = TextField(lazy_gettext(u'Search'), [validators.required()])
    page = IntegerField(lazy_gettext(u'Page'), default=1)

    # dynamc fields
    author = TextField(lazy_gettext(u'Author'), [validators.optional(),
        validators.is_user()],
        widget=widgets.AutocompleteWidget('api/core/get_user'))
    tags = AutocompleteField(lazy_gettext(u'Tags'), get_label='name',
                        query_factory=lambda: Tag.query)
    date = DatePeriodField(lazy_gettext(u'Date'))


def get_change_password_form(request):
    random_pw = get_random_password() if 'random' in request.args else None

    class ChangePasswordForm(Form):

        old_password = PasswordField(lazy_gettext(u'Old Password'),
                                     [validators.required()])
        new_password = PasswordField(lazy_gettext(u'New Password'),
                                     [validators.required()],
                                     default=random_pw,
                                     widget=widgets.PasswordInput(False))
        new_password_confirm = PasswordField(lazy_gettext(u'New Password (confirmation)'),
            [validators.equal_to('new_password', message=lazy_gettext(u'Passwords must match'))],
            default=random_pw, widget=widgets.PasswordInput(False))

    return ChangePasswordForm


class DeactivateProfileForm(Form):
    password = PasswordField(lazy_gettext(u'Password'),
            [validators.required()],
            widget=widgets.PasswordInput(False))
