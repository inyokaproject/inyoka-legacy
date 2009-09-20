# -*- coding: utf8 -*-
"""
    inyoka.utils.confirm
    ~~~~~~~~~~~~~~~~~~~~

    Provides various utilities to store confirmation data in the database and
    retrieve it.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import string
from datetime import date, datetime, timedelta
from random import sample
from inyoka.core.api import href, db


CONFIRM_ACTIONS = {}

confirm_table = db.Table('core_confirm', db.metadata,
    db.Column('id', db.Integer, primary_key=True),
    db.Column('key', db.String(40), unique=True),
    db.Column('action', db.String(40)),
    db.Column('data', db.PickleType),
    db.Column('expires', db.Date),
)


class Confirm(db.Model):
    key_length = 40
    key_chars = string.ascii_letters + string.digits

    def __init__(self, action, data, expires):
        self.key = Confirm._make_key()
        self.action = action
        self.data = data
        self.expires = expires

    def __repr__(self):
        return '<Confirm %s %s>' % (self.action, self.key)

    @classmethod
    def _make_key(cls):
        #TODO: maybe this should be done in before_insert
        return ''.join(sample(cls.key_chars, cls.key_length))

    @property
    def url(self):
        return href('portal/confirm', key=self.key)


def register_confirm(key):
    """
    Decorator to register a function that is called when a confirm link is
    accessed.

    :param key: The key which identifies the decorated function. It it stored
                in the database and used to relate the dataset with the
                function, so it must never ever change.

    Example::
        @register_confirm('change_email')
        def confirm_change_email(data):
            user = User.query.get(data['user_id'])
            user.email = data['email']
            session.commit()
    """
    def _register_confirm(f):
        assert key not in CONFIRM_ACTIONS, 'duplicate entry: %s' % key
        CONFIRM_ACTIONS[key] = f
        return f
    return _register_confirm


def store_confirm(action, timeout, data):
    """
    Save confirm data to the database.

    :param action: The key of the wanted action (as specified in
                   `register_confirm`)
    :param timeout: Defines when the confirm should expire. This is only
                    accurate to one day. This may either be a datetime or date,
                    a timedelta or an integer, which is then considered the
                    time until expiration in days.
    :param data: Data which is passed to the registered function when the link
                 is accessed. It is saved pickled, so make sure your object is
                 pickleable.

    Returns the confirm object.

    Example::
        def change_email(request):
            if request.method == 'POST':
                c = store_confirm('change_email', 7, {'user': request.user.id,
                        'email': request.POST['email'])
                send_mail(request.user, 'Please confirm your email address',
                          'Please click %s' % c.url)
    """
    if isinstance(timeout, (datetime, date)):
        expires = timeout
    if isinstance(timeout, timedelta):
        expires = timeout + expires
    else:
        expires = date.today() + timedelta(days=timeout)

    if not action in CONFIRM_ACTIONS:
        raise KeyError('Action %r is not registered.' % action)

    c = Confirm(action, data, expires)
    confirm_objects[c.key] = c
    db.session.commit()
    return c

def call_confirm(key):
    """
    Fetch the confirm entry with the specified key from the database, call
    the registered function and if there were no errors, delete the entry.
    """
    try:
        c = Confirm.query.filter_by(key=key).one()
    except InvalidRequestError:
        raise KeyError('No such key')
    if c.expires < date.today():
        raise KeyError('Key expired')
    ret = CONFIRM_ACTIONS[c.action](c.data)
    db.session.delete(c)
    db.session.commit()
    return ret

