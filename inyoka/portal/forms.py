# -*- coding: utf-8 -*-
"""
    inyoka.portal.forms
    ~~~~~~~~~~~~~~~~~

    Formulars for the portal.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core import forms
from inyoka.core.database import db
from inyoka.core.forms.utils import model_to_dict, update_model
from inyoka.i18n import _
from inyoka.portal import IUserProfileExtender
from inyoka.portal.models import UserProfile

# Eks ;)
def get_profile_form():
    class ProfileForm(forms.Form):
        def __init__(self, *args, **kwargs):
            self.profile = profile = kwargs.pop('profile')
            if profile is not None:
                profile_fields = IUserProfileExtender.get_profile_names()
                kwargs['initial'] = model_to_dict(profile, fields=profile_fields)
            super(ProfileForm, self).__init__(*args, **kwargs)

        def save(self, commit=True):
            profile = UserProfile() if self.profile is None else self.profile
            profile_fields = IUserProfileExtender.get_profile_names()
            profile = update_model(profile, self, profile_fields)
            if commit:
                db.session.commit()
            return profile


    for field in IUserProfileExtender.get_profile_names():
        ProfileForm.fields[field] = forms.TextField(field, max_length=255, required=True)

    return ProfileForm
