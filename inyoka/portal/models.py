# -*- coding: utf-8 -*-
"""
    inyoka.portal.models
    ~~~~~~~~~~~~~~~~~~~~

    Models for the portal.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.database import db
from inyoka.portal import IUserProfileExtender

class BasicProfile(IUserProfileExtender):
    properties = {
        'real_name': db.Column(db.String(200), nullable=False, default=''),
    }
