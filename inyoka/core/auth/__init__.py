# -*- coding: utf-8 -*-
"""
    inyoka.core.auth
    ~~~~~~~~~~~~~~~~

    Inyoka authentication framework.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from __future__ import with_statement

from threading import Lock

from werkzeug import import_string
from inyoka import Component
from inyoka.core.config import config
from inyoka.core.middlewares import IMiddleware
from inyoka.core import forms
from inyoka.core.templating import templated
from inyoka.core.i18n import lazy_gettext


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


class LoginUnsucessful(Exception):
    """Raised if the login failed."""


class StandardLoginForm(forms.Form):
    """Used to log in users."""
    username = forms.TextField(lazy_gettext(u'Username'), required=True)
    password = forms.TextField(lazy_gettext(u'Password'), required=True,
                               widget=forms.widgets.PasswordInput)

    def __init__(self, initial=None, action=None, request=None):
        forms.Form.__init__(self, initial, action, request)
        self.auth_system = get_auth_system()
        if self.auth_system.passwordless:
            del self.fields['password']


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
            flag = comp.has_perm(user, perm, obj)
            # The component doesn't care about the permission.
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

    def __unicode__(self):
        return self.display_name


class AnonymousUser(User):
    def __init__(self):
        super(AnonymousUser, self).__init__(0, u'anonymous', u'Anonymous')
        self.anonymous = True


class AuthSystemBase(object):
    """The base auth system.

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
    should happen transparently for the user.  eg, the user has already
    registered somewhere else and the Solace account is created based on the
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


    def get_login_form(self):
        """Returns the login form."""
        return StandardLoginForm()

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
        returns a response object, Solace will abort standard registration
        handling.
        """

    def register(self, request, username, password, email):
        """Called like a view function with only the request.  Has to do the
        register heavy-lifting.  Auth systems that only use the internal
        database do not have to override this method.  Implementers that
        override this function *have* to call `after_register` to finish
        the registration of the new user.  If `before_register` is unnused
        it does not have to be called, otherwise as documented.
        """
        rv = auth.before_register(request)
        if rv is not None:
            return rv

        #form = RegistrationForm()
        #if request.method == 'POST' and form.validate():
        #    user = User(form['username'], form['email'], form['password'])
        #    self.after_register(request, user)
        #    session.commit()
        #    if rv is not None:
        #        return rv
        #    return form.redirect('kb.overview')
        #return render_template('core/register.html', form=form.as_widget())

    def after_register(self, request, user):
        """Handles activation."""
        #if settings.REGISTRATION_REQUIRES_ACTIVATION:
        #    user.is_active = False
        #    confirmation_url = url_for('core.activate_user', email=user.email,
        #                               key=user.activation_key, _external=True)
        #    send_email(_(u'Registration Confirmation'),
        #               render_template('mails/activate_user.txt', user=user,
        #                               confirmation_url=confirmation_url),
        #               user.email)
        #    request.flash(_(u'A mail was sent to %s with a link to finish the '
        #                    u'registration.') % user.email)
        #else:
        #    request.flash(_(u'You\'re registered.  You can login now.'))

    def before_login(self, request):
        """If this login system uses an external login URL, this function
        has to return a redirect response, otherwise None.  This is called
        before the standard form handling to allow redirecting to an
        external login URL.  This function is called by the default
        `login` implementation.

        If the actual login happens here because of a back-redirect the
        system might raise a `LoginUnsucessful` exception.
        """

    def login(self, request):
        """Like `register` just for login."""
        form = self.get_login_form()

        # some login systems require an external login URL.  For example
        # the one we use as Plurk.
        try:
            rv = self.before_login(request)
            if rv is not None:
                return rv
        except LoginUnsucessful, e:
            form.add_error(unicode(e))

        # only validate if the before_login handler did not already cause
        # an error.  In that case there is not much win in validating
        # twice, it would clear the error added.
        if form.is_valid and request.method == 'POST' and form.validate(request.form):
            try:
                rv = self.perform_login(request, **form.data)
            except LoginUnsucessful, e:
                form.add_error(unicode(e))
            else:
#                session.commit()
                if rv is not None:
                    return rv
#                request.flash(_(u'You are now logged in.'))
                return form.redirect('portal/index')

        return self.render_login_template(request, form)

    def perform_login(self, request, **form_data):
        """If `login` is not overridden, this is called with the submitted
        form data and might raise `LoginUnsucessful` so signal a login
        error.
        """
        raise NotImplementedError()


    @templated('portal/login.html')
    def render_login_template(self, request, form):
        """Renders the login template"""
        return { 'login_form':form.as_widget() }


    def logout(self, request):
        """This has to logout the user again.  This method must not fail.
        If the logout requires the redirect to an external resource it
        might return a redirect response.  That resource then should not
        redirect back to the logout page, but instead directly to the
        **current** `request.next_url`.

        Most auth systems do not have to implement this method.  The
        default one calls `set_user(request, None)`.
        """
        self.set_user(request, None)


    def get_user(self, request):
        raise NotImplementedError()


    def set_user(self, request, user):
        """Can be used by the login function to set the user.  This function
        should only be used for auth systems internally if they are not using
        an external session.
        """
        if user is None:
            request.session.pop('user_id', None)
        else:
            #user.last_login = datetime.utcnow()
            request.session['user_id'] = user.id
