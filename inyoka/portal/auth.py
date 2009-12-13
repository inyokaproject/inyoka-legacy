# -*- coding: utf-8 -*-
"""
    inyoka.portal.auth
    ~~~~~~~~~~~~~~~~~~

    Some description here

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import db
from inyoka.core.http import redirect_to
from inyoka.core.auth import AuthSystemBase, LoginUnsucessful
from inyoka.core.auth.models import User


class EasyAuth(AuthSystemBase):
    def perform_login(self, request, username, password, permanent=False):
        try:
            user = User.query.get(username)
        except db.NoResultFound:
            raise LoginUnsucessful('This username doesn\'t exist.')
        if user.check_password(password):
            self.set_user(request, user)
            if permanent:
                request.session['_permanent_session'] = True
            return redirect_to('portal/index')
        else:
            raise LoginUnsucessful('The password is not correct.')

    def get_user(self, request):
        if request.session.get('user_id'):
            return User.query.get(request.session.get('user_id'))
        else:
            return User.query.get(u'anonymous')

    def set_user(self, request, user):
        if user is None:
            request.session.pop('user_id', None)
            request.session.pop('_permanent_session', None)
        else:
            request.session['user_id'] = user.id
