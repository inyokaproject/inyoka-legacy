# -*- coding: utf-8 -*-
"""
    inyoka.portal.models
    ~~~~~~~~~~~~~~~~~~~~

    Models for the portal.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core import auth
from inyoka.core.database import db

class UserProfile(db.Model):
    __tablename__ = 'portal_userprofile'
    __extendable__ = True

    user_id = db.Column(db.ForeignKey(auth.User.id), primary_key=True)
    user = db.relation(auth.User, backref='profile')


class ProfileSchemaController(db.ISchemaController):
    models = [UserProfile]
