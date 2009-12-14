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

from sqlalchemy.orm.exc import NoResultFound
from werkzeug import import_string
from inyoka import Component
from inyoka.i18n import _
from inyoka.core.auth import forms, models
from inyoka.core.auth.models import User
from inyoka.core.context import config
from inyoka.core.database import db
from inyoka.core.http import redirect_to, Response
from inyoka.core.middlewares import IMiddleware
from inyoka.core.models import Confirm
from inyoka.core.templating import templated
from inyoka.utils.confirm import register_confirm

_auth_system = None
_auth_system_lock = Lock()


def get_auth_system():
    """Return the auth system."""
    global _auth_system
    with _auth_system_lock:
        if _auth_system is None:
            _auth_system = import_string(config['auth.system'])()
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
        return forms.StandardLoginForm(self)

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

    @templated('portal/register.html')
    def register(self, request):
        """Called like a view function with only the request.  Has to do the
        register heavy-lifting.  Auth systems that only use the internal
        database do not have to override this method.  Implementers that
        override this function *have* to call `after_register` to finish
        the registration of the new user.  If `before_register` is unnused
        it does not have to be called, otherwise as documented.
        """
        rv = self.before_register(request)
        if rv is not None:
            return rv

        form = forms.RegistrationForm()
        if request.method == 'POST' and form.validate(request.form):
            user = User(username=form['username'], email=form['email'],
                        password=form['password'])
            db.session.add(user)
            r = self.after_register(request, user)
            db.session.commit()
            if isinstance(r, Response):
                return r
            return redirect_to('portal/index')
        return {'form':form.as_widget()}

    def after_register(self, request, user):
        """
        Tasks to be performed after the registration.
        Per default this sends an activation email.
        """
        return self.send_activation_mail(request, user)

    def send_activation_mail(self, request, user):
        """Sends an activation mail."""
        print 'send activation mail called'
#        if settings.REGISTRATION_REQUIRES_ACTIVATION:
        if True:
            db.session.commit()
            c = Confirm('activate_user', {'user': user.id}, 3)
            db.session.add(c)
            db.session.commit()
#            send_email(_(u'Registration Confirmation'), user,
#                       render_template('mails/activate_user.txt', user=user,
#                                       confirmation_url=c.url))
#            flash(_(u'An email was sent with a link to finish the '
#                    u'registration.'))
#            return redirect_to('portal/index')
            return Response('activation link: %s' % c.url)
        else:
            user.status = 'normal'
            db.session.commit()
#            flash(_(u'You\'re registered.  You can login now.'))
            return redirect_to('portal/login')

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
        if request.method == 'POST' and form.validate(request.form):
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


@register_confirm('activate_user')
def activate_user(data):
    try:
        u = User.query.get(data['user'])
    except NoResultFound:
#        flash(_('User not found.'))
        print 'not found'
        return redirect_to('portal/index')
    u.status = 'normal'
    db.session.commit()
    # flash(_('Registration confirmed. You may login now.'))
    return redirect_to('portal/login')
