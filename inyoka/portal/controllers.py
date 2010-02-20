# -*- coding: utf-8 -*-
"""
    inyoka.portal.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the portal app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IController, Rule, view, Response, \
    templated, href, redirect_to, _
from inyoka.core.auth import get_auth_system
from inyoka.core.auth.models import User
from inyoka.core.context import ctx
from inyoka.core.database import db
from inyoka.utils.confirm import call_confirm, Expired
from inyoka.portal.models import UserProfile, IUserProfileExtender


class PortalController(IController):
    name = 'portal'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/login/', endpoint='login'),
        Rule('/logout/', endpoint='logout'),
        Rule('/register/', endpoint='register'),
        Rule('/confirm/<key>/', endpoint='confirm'),
        Rule('/users/', endpoint='users'),
        Rule('/user/<username>/', endpoint='profile'),
        Rule('/usercp/profile/', endpoint='profile_edit'),
    ]

    @view
    @templated('portal/profile_edit.html')
    def profile_edit(self, request):
        profile = UserProfile.query.filter_by(user_id=request.user.id).first()
        form = forms.get_profile_form()(profile=profile)

        if request.method == 'POST' and form.validate(request.form):
            form.save()
            request.flash(_(u'Profile saved'), True)

        print form.as_widget().hidden_fields
        return {'form':form.as_widget()}

    @view
    @templated('portal/index.html')
    def index(self, request):
        return {'called_url': request.current_url,
                 'link': href('portal/index')}

    @view
    @templated('portal/users.html')
    def users(self, request):
        return {'users': User.query}

    @view
    @templated('portal/profile.html')
    def profile(self, request, username):
        user, profile = db.session.query(User, UserProfile).outerjoin(UserProfile).\
                            filter(User.username==username).one()
        data = {
            'user': user,
            'profile': profile,
            'fields': IUserProfileExtender.get_profile_names(),
        }
        return data

    @view
    @templated('portal/login.html')
    def login(self, request):
        return get_auth_system().login(request)

    @view
    def logout(self, request):
        get_auth_system().logout(request)
        return redirect_to('portal/index')

    @view
    def register(self, request):
        return get_auth_system().register(request)

    @view
    def confirm(self, request, key):
        try:
            ret = call_confirm(key)
        except KeyError:
            ret = _('Key not found. Maybe it has already been used?'), False
        except Expired:
            ret = _('The supplied key is not valid anymore.'), False

        if isinstance(ret, tuple) and len(ret) == 2:
            # flash(*ret)
            # return redirect_to('portal/index')
            return Response('%s: %s' % (['success', 'fail'][not ret[1]],
                                        ret[0]), mimetype='text/plain')
        return ret



class CalendarController(IController):
    name = 'calendar'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/<date:date>/<slug>/', endpoint='entry'),
    ]

    @view('index')
    def index(self, request):
        return Response('this is calendar index page')

    @view('entry')
    def entry(self, request, date, slug):
        return Response('this is calendar entry %r from %r' % (slug, date))
