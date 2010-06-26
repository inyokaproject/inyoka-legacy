# -*- coding: utf-8 -*-
"""
    inyoka.portal.auth
    ~~~~~~~~~~~~~~~~~~

    Some description here

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import db, _, ctx, lazy_gettext
from inyoka.core.http import redirect_to, Response
from inyoka.core.exceptions import abort
from inyoka.core.auth import IAuthSystem, LoginUnsucessful
from inyoka.core.auth.models import User
from inyoka.core.templating import templated
from inyoka.core.models import Confirm
from inyoka.portal.forms import LoginForm, RegistrationForm
from inyoka.utils.confirm import register_confirm



@register_confirm('activate_user')
def activate_user(data):
    try:
        u = User.query.get(data['user'])
    except db.NoResultFound:
        return redirect_to('portal/index')
    u.status = 'normal'
    db.session.commit()
    ctx.current_request.flash(_(
        u'Activation successfull, you can now login with your credentials'
    ))
    return redirect_to('portal/login')


class EasyAuth(IAuthSystem):
    """Auth system that uses the user model for authentication.

    It also supports permanent sessions using the `_permanent_session`
    key in the current session.
    """

    login_failed_message = _(u'User is unknown or the password is not correct.')


    def get_login_form(self, request, default=None):
        """Returns the login form."""
        default = {} if default is None else default
        return LoginForm(self, request.form, **default)

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

        form = RegistrationForm(request.form)
        if request.method == 'POST' and form.validate():
            user = User(username=form.username.data, email=form.email.data,
                        password=form.password.data)
            db.session.commit()
            r = self.after_register(request, user)
            if isinstance(r, Response):
                return r
            return redirect_to('portal/index')
        return {'form': form}

    def after_register(self, request, user):
        """
        Tasks to be performed after the registration.
        Per default this sends an activation email.
        """
        from celery.execute import send_task
        # send the activation email.
        c = Confirm('activate_user', {'user': user.id}, 3)
        db.session.commit()
        send_task('inyoka.core.tasks.send_activation_mail', [user.id, c.url])

    def login(self, request):
        """Like `register` just for login."""
        form = self.get_login_form(request)

        # some login systems require an external login URL.
        try:
            rv = self.before_login(request)
            if rv is not None:
                return rv
        except LoginUnsucessful, e:
            request.flash(lazy_gettext(unicode(e)), False)

        # only validate if the before_login handler did not already cause
        # an error.  In that case there is not much win in validating
        # twice, it would clear the error added.
        if request.method == 'POST' and form.validate():
            try:
                rv = self.perform_login(request, **form.data)
            except LoginUnsucessful, e:
                request.flash(lazy_gettext(unicode(e)), False)
            else:
                if rv is not None:
                    return rv
                request.flash(_(u'You are now logged in.'), True)
                return form.redirect('portal/index')

        return self.render_login_template(request, form)

    @templated('portal/login.html')
    def render_login_template(self, request, form):
        """Renders the login template"""
        return {'login_form': form}

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
        request.flash(_(u'You have been logged out successfully.'), True)

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


class HttpBasicAuth(EasyAuth):
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
        _message, _code = _(u'Please log in.'), 401

        # Try to get an already logged in user
        if request.session.get('user_id', None):
            return redirect_to('portal/index')

        if request.authorization:
            auth = request.authorization
            try:
                user = User.query.get(auth.username)
                if user.check_password(request.authorization.password):
                    self.set_user(request, user)
                    request.flash(_(u'You are now logged in.'), True)
                    return redirect_to('portal/index')
                else:
                    _message, _code = _(u'Invalid login.'), 403
            except db.NoResultFound:
                _message, _code = _(u'Invalid login'), 403

        # ask for login
        response = Response(_message, _code,
            {'WWW-Authenticate': 'Basic realm="%s' % self.realm})
        abort(response)
