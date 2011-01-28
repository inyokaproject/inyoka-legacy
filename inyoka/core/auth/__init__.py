# -*- coding: utf-8 -*-
"""
    inyoka.core.auth
    ~~~~~~~~~~~~~~~~

    Inyoka authentication framework.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from threading import Lock
from werkzeug import import_string
from inyoka import Interface
from inyoka.context import ctx
from inyoka.core.middlewares import IMiddleware


_auth_system = None
_auth_system_lock = Lock()


def get_auth_system():
    """Return the auth system currently configured.

    If you want to refresh the auth system call :func:`refresh_auth_system`.
    """
    global _auth_system
    with _auth_system_lock:
        if _auth_system is None:
            _auth_system = import_string(ctx.cfg['auth.system'])()
        return _auth_system


def refresh_auth_system():
    """Tears down the auth system after a config change."""
    global _auth_system
    with _auth_system_lock:
        _auth_system = None


class LoginUnsucessful(Exception):
    """Raised if the login failed."""


class AuthMiddleware(IMiddleware):
    priority = 75

    def process_request(self, request):
        auth = get_auth_system()
        user = auth.get_user(request)

        request.user = user

    def process_response(self, request, response):
        if not request.user.is_anonymous:
            response.prevent_caching()

        return response


class IAuthSystem(Interface):
    """The base auth system interface.

    Most functionality is described in the methods and properties you have
    to override for subclasses.  A special notice applies for user
    registration.

    Different auth systems may create users at different stages (first login,
    register etc.).  At that point (where the user is created in the
    database) the system has to call `after_register` and pass it the user
    (and request) object.  That method handles the confirmation mails and
    whatever else is required.  If you do not want your auth system to send
    confirmation mails you still have to call the method but tell the user
    of your class to disable registration activation in the configuration.

    `after_register` should *not* be called if the registration process
    should happen transparently for the user.  Eg, the user has already
    registered somewhere else and the Inyoka account is created based on the
    already existing account on first login.
    """

    #: for auth systems that are managing the email externally this
    #: attributes has to set to `True`.  In that case the user will
    #: be unable to change the email from the profile.  (True for
    #: the plurk auth, possible OpenID support and more.)
    email_managed_external = False

    #: like `email_managed_external` but for the password
    password_managed_external = False

    #: set to True to indicate that this login system does not use
    #: a password.  This will also affect the standard login form.
    passwordless = False

    #: if you don't want to see a register link in the user interface
    #: for this auth system, you can disable it here.
    show_register_link = True

    @property
    def can_reset_password(self):
        """You can either override this property or leave the default
        implementation that should work most of the time.  By default
        the auth system can reset the password if the password is not
        externally managed and not passwordless.
        """
        return not (self.passwordless or self.password_managed_external)

    def before_register(self, request):
        """Invoked before the standard register form processing.  This is
        intended to be used to redirect to an external register URL if
        if the syncronization is only one-directional.  If this function
        returns a response object, Inyoka will abort standard registration
        handling.
        """

    def register(self, request):
        """Called like a view function with only the request.  Has to do the
        register heavy-lifting.

        This method should, but don't have to call :meth:`before_register` and
        :meth:`after_register` to either check if the register process is
        not required or to finish the user registration.

        :param request: The current request object.
        """

    def after_register(self, request, user):
        """Tasks to be performed after the registration."""

    def before_login(self, request):
        """If this login system uses an external login URL, this function
        has to return a redirect response, otherwise None.  This is called
        before the standard form handling to allow redirecting to an
        external login URL.

        If the actual login happens here because of a back-redirect the
        system might raise a `LoginUnsucessful` exception.
        """

    def login(self, request):
        """Called like a view function with only the request.  Has to do the
        login heavy-lifting.

        This method should, but don't have to call :meth:`before_login` and
        :meth:`after_register` to either check if the login process is
        not required or finish the user login.

        :param request: The current request object.
        """

    def perform_login(self, request, **form_data):
        """If `login` is not overridden, this is called with the submitted
        form data and might raise `LoginUnsucessful` so signal a login
        error.
        """

    def logout(self, request):
        """This has to logout the user again.  This method must not fail.
        If the logout requires the redirect to an external resource it
        might return a redirect response.  That resource then should not
        redirect back to the logout page, but instead directly to the
        **current** `request.next_url`.

        Most auth systems do not have to implement this method.
        """

    def get_user(self, request):
        """Return the current user from the request object."""

    def set_user(self, request, user):
        """Can be used by the login function to set the user.  This function
        should only be used for auth systems internally if they are not using
        an external session.
        """
