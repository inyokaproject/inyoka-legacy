# -*- coding: utf-8 -*-
"""
    inyoka.portal.models
    ~~~~~~~~~~~~~~~~~~~~

    Models for the portal.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from wtforms import TextField, widgets, validators
from sqlalchemy.util import classproperty
from inyoka import Interface
from inyoka.core.api import _, db, ctx
from inyoka.core.auth.models import User, IUserProfileExtender
from inyoka.utils.forms import is_valid_url, is_valid_jabber


class BasicProfile(IUserProfileExtender):
    """Profile extender to add basic profile properties
    to the user profile model.
    """
    profile_properties = {
        'real_name': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'Realname'), max_length=200),
        },
        'website': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'Website'), validators=[is_valid_url()])
        },
        'location': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'Location'), max_length=200),
        },
        'interests': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'Interests'), max_length=200),
        },
        'occupation': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'Occupation'), max_length=200),
        },
        'signature': {
            'column': db.Column(db.Text),
            'form': TextField(_(u'Signature'), widget=widgets.TextArea())
        },
        'jabber': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'Jabber ID'), validators=[is_valid_jabber()]),
        },
        'skype': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'Skype'), max_length=25),
        },
        'qutecom': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'QuteCom (previously called WengoPhone)'),
                                    max_length=200)
        },
        'sip': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'SIP'), max_length=25)
        }
    }
