# -*- coding: utf-8 -*-
"""
    inyoka.portal.auth
    ~~~~~~~~~~~~~~~~~~

    Some description here

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.routing import href
from inyoka.core.auth import AuthSystemBase, LoginUnsucessful
from inyoka.core.http import redirect
from inyoka.core.models import User
from inyoka.core.api import db


class EasyAuth(AuthSystemBase):
    def perform_login(self, request, username, password):
        try:
            user = User.query.get(username)
        except db.NoResultFound:
            raise LoginUnsucessful('This username doesn\'t exist.')
        if user.check_password(password):
            self.set_user(request, user)
            return redirect(href('portal/index'))
        else:
            raise LoginUnsucessful('The password is not correct.')

    def get_user(self, request):
        if request.session.get('user_id'):
            return User.query.get(request.session.get('user_id'))
        else:
            return User.query.get(u'anonymous')
