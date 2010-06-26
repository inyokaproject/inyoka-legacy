# -*- coding: utf-8 -*-
"""
    inyoka.portal.models
    ~~~~~~~~~~~~~~~~~~~~

    Models for the portal.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.forms import TextField, widgets, validators
from inyoka.core.api import _, db
from inyoka.core.auth.models import IUserProfileExtender


class BasicProfile(IUserProfileExtender):
    """Profile extender to add basic profile properties
    to the user profile model.
    """
    profile_properties = {
        'real_name': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'Realname'), [validators.Length(max=200)]),
        },
        'website': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'Website'), validators=[validators.is_valid_url()])
        },
        'location': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'Location'), [validators.Length(max=200)]),
        },
        'interests': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'Interests'), [validators.Length(max=200)]),
        },
        'occupation': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'Occupation'), [validators.Length(max=200)]),
        },
        'signature': {
            'column': db.Column(db.Text),
            'form': TextField(_(u'Signature'), widget=widgets.TextArea())
        },
        'jabber': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'Jabber ID'), validators=[validators.is_valid_jabber()]),
        },
        'skype': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'Skype'), [validators.Length(max=25)]),
        },
        'qutecom': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'QuteCom (previously called WengoPhone)'),
                              [validators.Length(max=200)])
        },
        'sip': {
            'column': db.Column(db.String(200)),
            'form': TextField(_(u'SIP'), [validators.Length(max=25)])
        }
    }
