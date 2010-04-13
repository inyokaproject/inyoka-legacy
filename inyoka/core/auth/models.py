# -*- coding: utf-8 -*-
"""
    inyoka.core.auth.models
    ~~~~~~~~~~~~~~~~~~~~~~~

    Models for the authentication system.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import random
from datetime import datetime

from inyoka import Interface
from inyoka.i18n import _
from inyoka.core.cache import cache
from inyoka.core.context import ctx
from inyoka.core.database import db, IModelPropertyProvider
from inyoka.core.serializer import SerializableObject
from inyoka.core.subscriptions import subscribed
from inyoka.utils.datastructures import BidiMap
from inyoka.utils.crypt import get_hexdigest


USER_STATUS_MAP = BidiMap({
    0: _('inactive'), #not yet activated
    1: _('normal'),
    2: _('banned'),
    3: _('deleted'), #deleted itself
})


class UserQuery(db.Query):
    def get(self, pk):
        if isinstance(pk, basestring):
            return self.filter_by(username=pk).one()
        return super(UserQuery, self).get(pk)

    def get_anonymous(self):
        user = cache.get('core/anonymous')
        if user is None:
            name = ctx.cfg['anonymous_name']
            user = User.query.get(name)
            cache.set('core/anonymous', user)
        user = db.session.merge(user, load=False)
        return user


class User(db.Model, SerializableObject):
    __tablename__ = 'core_user'

    query = db.session.query_property(UserQuery)

    # serializer properties
    object_type = 'inyoka.user'
    public_fields = ('id', 'username', 'pw_hash', 'status', 'real_name')

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
    pw_hash = db.Column(db.String(60))
    # The day the user registered itself
    date_joined = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # The day the user recently joined the webpage
    last_login = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # the status of the user. 0: inactive, 1: normal, 2: banned, 3: deleted
    _status = db.Column('status', db.Integer, nullable=False, default=0)


    def __init__(self, username, email, password=''):
        self.username = username
        self.email = email
        self.set_password(password)
        db.session.add(self)

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
        name = ctx.cfg['anonymous_name']
        return self.username == name

    def subscribed(self, name, subject_id=None):
        return subscribed(name, self, subject_id)

    def __repr__(self):
        i = '#%d' % self.id if self.id else '[no id]'
        return '<User %s %r>' % (i, self.username)

    def __unicode__(self):
        return self.display_name


class UserSchemaController(db.ISchemaController):
    models = [User]
