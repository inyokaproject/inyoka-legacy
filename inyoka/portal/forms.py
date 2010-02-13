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

class ProfileForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.user = user = kwargs.pop('user')
        self.profile_fields = fields = IUserProfileExtender.get_profile_names()
        kwargs['initial'] = model_to_dict(user, fields=fields)
        super(ProfileForm, self).__init__(*args, **kwargs)
        for field in fields:
            self.add_field(field, forms.TextField(field, max_length=255,
                                                  required=True))

    def save(self, commit=True):
        user = update_model(self.user, self, self.profile_fields)
        if commit:
            db.session.commit()
        return user
