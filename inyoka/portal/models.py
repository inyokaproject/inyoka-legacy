# -*- coding: utf-8 -*-
"""
    inyoka.portal.models
    ~~~~~~~~~~~~~~~~~~~~

    Models for the portal.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka import Interface
from inyoka.core.api import auth, db, ctx


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
    user = db.relation(auth.User, backref=db.backref(
        'profile', uselist=False))

    def get_url_values(self, action='view'):
        values = {
            'view':     ('portal/profile', {'username': self.user.username}),
            'edit':     ('portal/profile_edit', {}),
        }

        return values[action][0], values[action][1]


class IUserProfileExtender(db.IModelPropertyProvider, Interface):
    model = UserProfile

    @classmethod
    def get_profile_names(cls, only_editable=False):
        fields = []
        for imp in ctx.get_implementations(cls):
            fields += imp.properties.keys()
        return fields


class BasicProfile(IUserProfileExtender):
    """Profile extender to add basic profile properties
    to the user profile model.
    """
    properties = {
        'real_name': db.Column(db.String(200)),
        'website': db.Column(db.String(200)),
        'signature': db.Column(db.Text)
    }


class ProfileSchemaController(db.ISchemaController):
    models = [UserProfile]
