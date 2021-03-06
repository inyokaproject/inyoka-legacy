# -*- coding: utf-8 -*-
"""
    inyoka.core.auth.models
    ~~~~~~~~~~~~~~~~~~~~~~~

    Models for the authentication system.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import random
from datetime import datetime
from werkzeug import cached_property

from inyoka.i18n import _
from inyoka.core.cache import cache
from inyoka.context import ctx
from inyoka.core.database import db
from inyoka.core.serializer import SerializableObject
from inyoka.core.subscriptions import subscribed
from inyoka.utils.datastructures import BidiMap
from inyoka.utils.crypt import get_hexdigest


USER_STATUS_MAP = BidiMap({
    0: _(u'inactive'), #not yet activated
    1: _(u'normal'),
    2: _(u'banned'),
    3: _(u'deleted'), #deleted itself
})


group_group = db.Table('core_group_group', db.metadata,
    db.Column('group_id', db.Integer, db.ForeignKey('core_group.id')),
    db.Column('parent_id', db.Integer, db.ForeignKey('core_group.id')),
)

user_group = db.Table('core_group_user', db.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('core_user.id')),
    db.Column('group_id', db.Integer, db.ForeignKey('core_group.id'))
)



class Group(db.Model):
    __tablename__ = 'core_group'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(40), unique=True)

    parents = db.relationship('Group', secondary=group_group,
        backref=db.backref('children', collection_class=set, lazy='subquery'),
        primaryjoin=(id == group_group.c.group_id),
        secondaryjoin=(group_group.c.parent_id == id),
        foreign_keys=[group_group.c.group_id, group_group.c.parent_id],
        collection_class=set,
        cascade='all')

    def get_parents(self):
        if not self.parents:
            return
        parents = []
        for group in self.parents:
            parents.append(group)
            if group.parents:
                parents.extend(group.get_parents())
        return parents

    @cached_property
    def grant_parent(self):
        return self.get_parents()[-1]

    def get_url_values(self, action='view'):
        values = {
            'view': 'portal/group',
        }
        return values[action], {'name': self.name}


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


class AutomaticUserProfile(db.MapperExtension):

    def before_insert(self, mapper, connection, instance):
        if instance.profile is None:
            instance.profile = UserProfile()


class User(db.Model, SerializableObject):
    __tablename__ = 'core_user'
    __mapper_args__ = {'extension': AutomaticUserProfile()}

    query = db.session.query_property(UserQuery)

    # serializer properties
    object_type = 'inyoka.user'
    public_fields = ('id', 'username', 'pw_hash', 'status', 'real_name')

    #: The internal ID of the user.  Even if an external Auth system is
    #: used, we're storing the users a second time internal so that we
    #: can easilier work with relations.
    id = db.Column(db.Integer, primary_key=True)

    #: The username of the user.  For external auth systems it makes a
    #: lot of sense to allow the user to chose a name on first login.
    username = db.Column(db.Unicode(40), unique=True)

    #: The email of the user.  If an external auth system is used, the
    #: login code should update that information automatically on login
    email = db.Column(db.Unicode(250), index=True, unique=True)

    #: The password hash.  This might not be used by every auth system.
    #: the OpenID auth for example does not use it at all.  But also
    #: external auth systems might not store the password here.
    pw_hash = db.Column(db.Unicode(60))

    #: When the user registered himself
    date_joined = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    #: When the user recently joined the webpage
    last_login = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    #: The status of the user. 0: inactive, 1: normal, 2: banned, 3: deleted
    _status = db.Column('status', db.Integer, nullable=False, default=0)

    groups = db.relationship(Group, secondary=user_group,
        backref=db.backref('users', lazy='dynamic'))

    def __init__(self, *args, **kwargs):
        # we just ignore applied pw_hashes so we calculate those ourselfs
        kwargs.pop('pw_hash', None)
        self.set_password(kwargs.pop('password', u''))
        db.Model.__init__(self, *args, **kwargs)

    def set_password(self, raw_password):
        """Set a new sha1 generated password hash"""
        salt = u'%05x' % random.getrandbits(20)
        hsh = get_hexdigest(salt, raw_password)
        self.pw_hash = u'%s$%s' % (salt, hsh)

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct.
        """
        salt, hsh = self.pw_hash.split(u'$')
        return hsh == get_hexdigest(salt, raw_password)

    def _set_status(self, status):
        self._status = USER_STATUS_MAP[status]
    def _get_status(self):
        return USER_STATUS_MAP[self._status]
    status = db.synonym('_status', descriptor=property(_get_status, _set_status))

    is_active = property(lambda self: self.status == u'normal')

    @property
    def display_name(self):
        return self.username

    @property
    def is_anonymous(self):
        name = ctx.cfg['anonymous_name']
        return self.username == name

    def subscribed(self, type, subject_id=None):
        return subscribed(type, self, subject_id)

    def get_url_values(self, action='profile'):
        if action == 'profile':
            return 'portal/profile', {'username': self.username}

    def deactivate(self):
        """Deactivates the user for ever. Use with care!!

        This method does not commit the changes to the database.
        """
        self._status = 3
        self.profile.clear()

    def __repr__(self):
        i = '#%d' % self.id if self.id else '[no id]'
        return '<User %s %r>' % (i, self.username)

    def __unicode__(self):
        return self.display_name


class UserProfile(db.Model):
    """The profile for an user.

    The user profile contains various information about the user
    e.g the real name, his website and various contact information.

    This model provides basic fields but is extendable to provide much
    more information if required.

    """
    __tablename__ = 'core_userprofile'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey(User.id))
    user = db.relationship(User, backref=db.backref('profile',
        uselist=False, lazy='joined', innerjoin=True))

    # profile properties.  We implement them here to get a better documented
    # and tested model structure.  Feel free to advance the attributes!

    # personal attributes
    real_name = db.Column(db.Unicode(200))
    website = db.Column(db.Unicode(200))
    location = db.Column(db.Unicode(200))
    interests = db.Column(db.Unicode(200))
    occupation = db.Column(db.Unicode(200))
    signature = db.Column(db.Text)

    # communication channels
    jabber = db.Column(db.Unicode(200))
    skype = db.Column(db.Unicode(200))

    def get_url_values(self, action='view'):
        values = {
            'view':     ('portal/profile', {'username': self.user.username}),
            'edit':     ('portal/profile_edit', {}),
        }

        return values[action][0], values[action][1]

    def clear(self):
        self.real_name = u''
        self.website = u''
        self.location = u''
        self.intersts = u''
        self.occupation = u''
        self.signature = u''
