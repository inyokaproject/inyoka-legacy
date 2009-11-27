# -*- coding: utf8 -*-
"""
    inyoka.utils.confirm
    ~~~~~~~~~~~~~~~~~~~~

    Provides various utilities to store confirmation data in the database and
    retrieve it.

    Usage example::
        def change_email(request):
            if request.method == 'POST':
                c = Confirm('change_email', 7, {
                        'user': request.user.id,
                        'email': request.POST['email']
                    })
                db.session.add(c)
                db.session.commit()
                send_mail(request.user, 'Confirm your email address',
                          'Please click this link: %s' % c.url)

        @register('change_email')
        def set_email(data):
            user = User.query.get(data['user'])
            if user is None:
                flash('This user has been deleted!')
            else:
                user.email = data['email']
                flash('Your email has been changed to %s' % data['email'])
            return redirect_to('portal/index')


    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
import string
from datetime import date, datetime, timedelta
from random import sample
from inyoka.core.database import db
from inyoka.core.models import Confirm
from inyoka.core.routing import href

CONFIRM_ACTIONS = {}
_key_re = re.compile('^[a-z_][a-z_0-9]*$', re.I)


class Expired(ValueError):
    """Raised by `call_confirm` when the confirm object has expired."""

class KeyNotFound(ValueError):
    """Raised by `call_confirm` when the supplied key is not found."""

def register_confirm(key):
    """
    Decorator to register a function that is called when a confirm link is
    accessed.

    :param key: The key which identifies the decorated function. It is stored
                in the database and used to relate the dataset with the
                function, so it must not change (at least not with in the
                expire time used for it).
    """
    assert key not in CONFIRM_ACTIONS, 'duplicate entry: %s' % key
    assert _key_re.match(key), 'key must only contain alnum and _ and not '\
                               'start with a digit'

    def _register_confirm(f):
        CONFIRM_ACTIONS[key] = f
        return f
    return _register_confirm


def store_confirm(action, data, expires):
    """
    Save confirm data to the database.

    This function just creates a Confirm object with the given data, stores it
    to the database and returns it.
    """
    c = Confirm(action, data, expires)
    db.session.add(c)
    db.session.commit()
    return c


def call_confirm(key):
    """
    Fetch the confirm entry with the specified key from the database and call
    the registered function, if the confirm key has not yet expired.
    """
    c = Confirm.query.get(key)
    if c is None:
        raise KeyNotFound('No such key: %s' % key)
    if c.is_expired:
        raise Expired('Expired on %s' % c.expires.strftime('%F'))
    ret = CONFIRM_ACTIONS[c.action](c.data)

    #TODO: maybe we should keep it for a while? (for error messages etc?)
    db.session.delete(c)
    db.session.commit()
    return ret
