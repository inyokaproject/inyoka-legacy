# -*- coding: utf-8 -*-
"""
    inyoka.portal.models
    ~~~~~~~~~~~~~~~~~~~~

    Models for the portal.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from sqlalchemy.util import classproperty
from inyoka import Interface
from inyoka.core import forms
from inyoka.core.api import _, auth, db, ctx
from inyoka.core.forms.validators import is_valid_url, is_valid_jabber
from inyoka.core.forms import widgets


class UserProfile(db.Model):
    """The profile for an user.

    The user profile contains various information about the user
    e.g the real name, his website and various contact information.

    This model provides basic fields but is extendable to provide much
    more information if required.

    To add new fields to the user profile implement the
    :class:`IUserProfileExtender` interface::

        class HardwareInformationProfile(IUserProfileExtender):
            properties = {
                'cpu': db.Column(db.String(200)),
                'gpu': db.Column(db.String(200))
                'mainboard': db.Column(db.String(200))
            }

    These fields are added to the user profile model on initialisation.
    """
    __tablename__ = 'portal_userprofile'
    __extendable__ = True

    user_id = db.Column(db.ForeignKey(auth.User.id), primary_key=True)
    user = db.relationship(auth.User,
        backref=db.backref('profile', uselist=False), innerjoin=True,
                           lazy='select')

    def get_url_values(self, action='view'):
        values = {
            'view':     ('portal/profile', {'username': self.user.username}),
            'edit':     ('portal/profile_edit', {}),
        }

        return values[action][0], values[action][1]


class IUserProfileExtender(db.IModelPropertyProvider, Interface):
    model = UserProfile
    profile_properties = {}

    @classproperty
    def properties(cls):
        return dict((k, cls.profile_properties[k]['column'])
                    for k in cls.profile_properties)

    @classmethod
    def get_all_properties(cls):
        props = {}
        for imp in ctx.get_implementations(cls):
            props.update(dict(
                (k, imp.profile_properties[k]['column']) for k in imp.profile_properties.keys()
            ))
        return props

    @classmethod
    def get_profile_names(cls):
        fields = []
        for imp in ctx.get_implementations(cls):
            fields += imp.profile_properties.keys()
        return fields

    @classmethod
    def get_profile_forms(cls):
        fields = {}
        for imp in ctx.get_implementations(cls):
            fields.update(dict(
                (k, imp.profile_properties[k]['form']) for k in imp.profile_properties.keys()
            ))
        return fields


class BasicProfile(IUserProfileExtender):
    """Profile extender to add basic profile properties
    to the user profile model.
    """
    profile_properties = {
        'real_name': {
            'column': db.Column(db.String(200)),
            'form': forms.TextField(_(u'Realname'), max_length=200),
        },
        'website': {
            'column': db.Column(db.String(200)),
            'form': forms.TextField(_(u'Website'), validators=[is_valid_url()])
        },
        'location': {
            'column': db.Column(db.String(200)),
            'form': forms.TextField(_(u'Location'), max_length=200),
        },
        'interests': {
            'column': db.Column(db.String(200)),
            'form': forms.TextField(_(u'Interests'), max_length=200),
        },
        'occupation': {
            'column': db.Column(db.String(200)),
            'form': forms.TextField(_(u'Occupation'), max_length=200),
        },
        'signature': {
            'column': db.Column(db.Text),
            'form': forms.TextField(_(u'Signature'), widget=widgets.Textarea)
        },
        'jabber': {
            'column': db.Column(db.String(200)),
            'form': forms.TextField(_(u'Jabber ID'), validators=[is_valid_jabber()]),
        },
        'skype': {
            'column': db.Column(db.String(200)),
            'form': forms.TextField(_(u'Skype'), max_length=25),
        },
        'qutecom': {
            'column': db.Column(db.String(200)),
            'form': forms.TextField(_(u'QuteCom (previously called WengoPhone)'),
                                    max_length=200)
        },
        'sip': {
            'column': db.Column(db.String(200)),
            'form': forms.TextField(_(u'SIP'), max_length=25)
        }
    }


class ProfileSchemaController(db.ISchemaController):
    models = [UserProfile]
