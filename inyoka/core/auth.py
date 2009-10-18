# -*- coding: utf-8 -*-
"""
    inyoka.core.auth
    ~~~~~~~~~~~~~~~~

    Inyoka authentication framework.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from threading import Lock
from werkzeug import import_string

from inyoka import Component
from inyoka.core.api import config
from inyoka.core.middlewares import IMiddleware

_auth_system = None
_auth_system_lock = Lock()

def get_auth_system():
    """Return the auth system."""
    global _auth_system
    with _auth_system_lock:
        if _auth_system is None:
            _auth_system = import_string(config['auth_system'])()
        return _auth_system

def refresh_auth_system():
    """Tears down the auth system after a config change."""
    global _auth_system
    with _auth_system_lock:
        _auth_system = None

class AuthMiddleware(IMiddleware):
    priority = 75

    def process_request(self, request):
        auth = get_auth_system()
        user = auth.get_user(request)
        if user is None:
            user = AnonymousUser()

        request.user = user

    def process_response(self, request, response):
        # TODO: set cache headers to no cache
        return response

class IPermissionChecker(Component):

    @classmethod
    def has_perm(cls, user, perm, obj=None):
        has_permission = False

        for comp in cls.get_components():
            # The component doesn't care about the permission.
            flag = comp.has_perm(user, perm, obj)
            if flag is None:
                continue
            # The component vetoed, which counts stronger than any True found.
            elif not flag:
                return False
            # We got an auth here, but we can't break out of the loop cause
            # another component still might veto.
            else:
                has_permission = True

        return has_permission



class User(object):
    def __init__(self, id, username, display_name):
        self.id = id
        self.username = username
        self.display_name = display_name
        self.anonymous = False

class AnonymousUser(User):
    def __init__(self):
        super(AnonymousUser, self).__init__(0, u'anonymous', u'Anonymous')
        self.anonymous = True

class AuthSystemBase(object):

    def login(self, request, username, password):
        """Has to perform the login.  If the login was successful with
        the credentials provided the function has to somehow make sure
        that the user is remembered.  Internal auth systems may use the
        `set_user` method.  If logging is is not successful the system
        has to raise an `LoginUnsucessful` exception.

        If the auth system needs the help of an external resource for
        login it may return a response object with a redirect code
        instead.  The user is then redirected to that page to complete
        the login.  This page then has to ensure that the user is
        redirected back to the login page to trigger this function
        again.  The back-redirect may attach extra argument to the URL
        which the function might want to used to find out if the login
        was successful.
        """
        raise NotImplementedError()

    def logout(self, request):
        """This has to logout the user again.  This method must not fail.
        If the logout requires the redirect to an external resource it
        might return a redirect response.  That resource then does not
        have to redirect back to the logout page, it might directly
        redirect to the `request.next_url`.

        Most auth systems do not have to implement this method.
        """

    def get_user(self, request):
        """If the user is logged in this method has to return the user
        object for the user that is logged in.

        If the user is not logged in, the return value has to be `None`.
        """
        raise NotImplementedError()

    def set_user(self, request, user):
        """Can be used by the login function to set the user.  This function
        should only be used for auth systems internally if they are not using
        an external session.
        """
        if user is None:
            request.session.pop('uuid')
        else:
            request.session['uuid'] = user.id

class EasyAuth(AuthSystemBase):
    _store = {}

    def login(self, request, username, password):
        user = User(username, username, username)
        self.set_user(request, user)
        self._store[user.id] = user

    def logout(self, request):
        del self._store[self.get_user(request).id]
        self.set_user(request, None)

    def get_user(self, request):
        return self._store.get(request.session.get('uuid'))
