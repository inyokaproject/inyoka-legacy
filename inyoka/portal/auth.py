# -*- coding: utf-8 -*-
"""
    inyoka.portal.auth
    ~~~~~~~~~~~~~~~~~~

    Some description here

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import db, _
from inyoka.core.http import redirect_to, Response
from inyoka.core.exceptions import abort
from inyoka.core.auth import AuthSystemBase, LoginUnsucessful
from inyoka.core.auth.models import User


class EasyAuth(AuthSystemBase):
    """Auth system that uses the user model for authentication.

    It also supports permanent sessions using the `_permanent_session`
    key in the current session.
    """

    login_failed_message = _(u'User is unknown or the password is not correct.')

    def perform_login(self, request, username, password, permanent=False):
        try:
            user = User.query.get(username)
        except db.NoResultFound:
            raise LoginUnsucessful(self.login_failed_message)
        if user.check_password(password):
            self.set_user(request, user)
            if permanent:
                request.session['_permanent_session'] = True
            request.flash(_(u'You are now logged in.'))
            return redirect_to('portal/index')
        else:
            raise LoginUnsucessful(self.login_failed_message)

    def get_user(self, request):
        if request.session.get('user_id'):
            return User.query.get(request.session.get('user_id'))
        else:
            return User.query.get_anonymous()

    def set_user(self, request, user):
        if user is None:
            request.session.pop('user_id', None)
            request.session.pop('_permanent_session', None)
        else:
            request.session['user_id'] = user.id


class HttpBasicAuth(AuthSystemBase):
    """Auth system that uses HTTP basic auth for authentication
    and queries the database for the proper username/password
    """
    realm = u'Inyoka'

    def get_user(self, request):
        if request.session.get('user_id'):
            return User.query.get(request.session.get('user_id'))
        else:
            return User.query.get_anonymous()

    def login(self, request):
        # Try to get an already logged in user
        if request.session.get('user_id', None):
            return redirect_to('portal/index')

        if request.authorization:
            auth = request.authorization
            try:
                user = User.query.get(auth.username)
                if user.check_password(request.authorization.password):
                    self.set_user(request, user)
                    request.flash(_(u'You are now logged in.'))
                    return redirect_to('portal/index')
            except db.NoResultFound:
                pass

        # ask for login
        response = Response(_(u'Please log in.'), 401,
            {'WWW-Authenticate': 'Basic realm="%s' % self.realm})
        abort(response)
