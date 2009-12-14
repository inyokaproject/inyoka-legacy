# -*- coding: utf-8 -*-
"""
    inyoka.core.auth.models
    ~~~~~~~~~~~~~~~~~~~~~~~

    Models for the authentication system.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import random

from inyoka.core.database import db
from inyoka.utils.datastructures import BidiMap
from inyoka.utils.crypt import get_hexdigest


USER_STATUS_MAP = BidiMap({
    0: 'inactive', #not yet activated
    1: 'normal',
    2: 'banned',
    3: 'deleted', #deleted itself
})


class UserQuery(db.Query):
    def get(self, pk):
        if isinstance(pk, basestring):
            return self.filter_by(username=pk).one()
        return super(UserQuery, self).get(pk)


class User(db.Model):
    __tablename__ = 'core_user'
    __extendable__ = True

    query = db.session.query_property(UserQuery)

    # the internal ID of the user.  Even if an external Auth system is
    # used, we're storing the users a second time internal so that we
    # can easilier work with relations.
    id = db.Column(db.Integer, primary_key=True)
    # the username of the user.  For external auth systems it makes a
    # lot of sense to allow the user to chose a name on first login.
    username = db.Column(db.String(40), unique=True)
    # the email of the user.  If an external auth system is used, the
    # login code should update that information automatically on login
    email = db.Column(db.String(200), index=True, unique=True)
    # the password hash.  This might not be used by every auth system.
    # the OpenID auth for example does not use it at all.  But also
    # external auth systems might not store the password here.
    pw_hash = db.Column(db.String(60), nullable=True)
    # the status of the user. 0: inactive, 1: normal, 2: banned, 3: deleted
    _status = db.Column('status', db.Integer, nullable=False, default=0)
    # the realname of the user.  This is also optional.
    real_name = db.Column(db.String(200), nullable=True)


    def __init__(self, username, email, password=''):
        self.username = username
        self.email = email
        self.set_password(password)

    def set_password(self, raw_password):
        """Set a new sha1 generated password hash"""
        salt = '%05x' % random.getrandbits(20)
        hsh = get_hexdigest(salt, raw_password)
        self.pw_hash = u'%s$%s' % (salt, hsh)

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct.
        """
        if isinstance(raw_password, unicode):
            raw_password = raw_password.encode('utf-8')
        salt, hsh = self.pw_hash.split('$')
        return hsh == get_hexdigest(salt, raw_password)

    def _set_status(self, status):
        self._status = USER_STATUS_MAP[status]
    def _get_status(self):
        return USER_STATUS_MAP[self._status]
    status = db.synonym('_status', descriptor=property(_get_status, _set_status))

    is_active = property(lambda self: self.status == 'normal')

    @property
    def display_name(self):
        return self.username

    @property
    def is_anonymous(self):
        # TODO: make configureable
        return True if self.username == 'anonymous' else False

    def __repr__(self):
        i = self.id and '#%d' % self.id or '(no id)'
        return '<User %s %r>' % (i, self.username)

    def __unicode__(self):
        return self.display_name
