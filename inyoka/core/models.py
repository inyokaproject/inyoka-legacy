# -*- coding: utf-8 -*-
"""
    inyoka.core.models
    ~~~~~~~~~~~~~~~~~~

    Core models not specific to a single app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import random
import string

from datetime import date, datetime, timedelta
from sqlalchemy.orm import MapperExtension
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from inyoka.core.database import db
from inyoka.core.routing import href


CONFIRM_ACTIONS = {}


class ConfirmMapperExtension(MapperExtension):
    def before_insert(self, mapper, connection, instance):
        while instance.key is None:
            key = mapper.class_._make_key()
            if Confirm.query.get(key) is None:
                instance.key = key


class ConfirmQuery(db.Query):
    def get(self, pk):
        if isinstance(pk, basestring):
            try:
                return self.filter_by(key=pk).one()
            except (NoResultFound, MultipleResultsFound):
                return None
        return super(ConfirmQuery, self).get(pk)


class Confirm(db.Model):
    """
    Holds the data for a confirm action.

    :param action: The key of the wanted action.
    :param expires: Defines when the confirm should expire. This is only
                    accurate to one day. This may either be a datetime or date,
                    a timedelta or an integer, which is then considered the
                    time until expiration in days. If the link is called after
                    it is expired, the user is rejected.
    :param data: Data which is passed to the registered function when the link
                 is accessed. It is saved pickled, so make sure your object is
                 pickleable.
    """

    __tablename__ = 'core_confirm'
    __mapper_args__ = {
        'extension': ConfirmMapperExtension(),
    }
    query = db.session.query_property(ConfirmQuery)

    _key_length = 32
    _key_chars = string.ascii_letters + string.digits

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), unique=True)
    action = db.Column(db.String(40))
    data = db.Column(db.PickleType)
    expires = db.Column(db.Date)

    def __init__(self, action, data, expires):
        if action not in CONFIRM_ACTIONS:
            raise KeyError('Action %r is not registered.' % action)

        if isinstance(expires, (datetime, date)):
            self.expires = expires
        elif isinstance(expires, timedelta):
            self.expires = date.today() + expires
        else:
            self.expires = date.today() + timedelta(days=expires)

        self.action = action
        self.data = data

    def __repr__(self):
        return '<Confirm %s %s>' % (self.action, getattr(self, 'key', ''))

    @classmethod
    def _make_key(cls):
        return ''.join(random.choice(cls._key_chars) for _
                       in range(cls._key_length))

    @property
    def url(self):
        return href('portal/confirm', key=self.key, _external=True)

    @property
    def is_expired(self):
        return self.expires < date.today()


class ConfirmSchemaController(db.ISchemaController):
    models = [Confirm]
