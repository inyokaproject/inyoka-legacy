# -*- coding: utf-8 -*-
"""
    inyoka.portal.forms
    ~~~~~~~~~~~~~~~~~~~

    Formulars for the portal.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from wtforms import Form, TextField, validators
from inyoka import Interface
from inyoka.core.database import db
from inyoka.i18n import _
from inyoka.core.auth.models import UserProfile, IUserProfileExtender
from inyoka.utils.forms import model_to_dict, update_model


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


class EditTagForm(Form):
    name = TextField(_(u'Name'), [validators.Length(max=20)])
