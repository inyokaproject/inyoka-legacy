# -*- coding: utf-8 -*-
"""
    inyoka.core.auth
    ~~~~~~~~~~~~~~~~

    Inyoka authentication framework.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka import Component


class IPermissionChecker(Component):

    @classmethod
    def has_perm(cls, user, perm):
        has_permission = False

        for comp in cls.get_components():
            # The component doesn't care about the permission.
            if comp.has_perm(user, perm) is None:
                continue
            # The component vetoed, which counts stronger than any True found.
            elif not comp.has_perm(user, perm):
                return False
            # We got an auth here, but we can't break out of the loop cause
            # another component still might veto.
            else:
                has_permission = True

        return has_permission


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
            request.session.pop('user_id')
        else:
            request.session['user_id'] = user.id


#class EasyAuth(AuthSystemBase):
#    def login(self, request, username, password):
#        user = User(username, username, username)
#        self.set_user(request, user)
#
#    def logout(self, request):
#        self.set_user(request, None)
