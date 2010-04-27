# -*- coding: utf-8 -*-
"""
    inyoka.portal.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the portal app.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sys
from inyoka.core.api import IController, Rule, view, Response, \
    templated, href, redirect_to, _
from inyoka.core.auth import get_auth_system
from inyoka.core.auth.models import User, UserProfile, IUserProfileExtender, \
    Group
from inyoka.core.models import Tag
from inyoka.core.context import ctx
from inyoka.core.database import db
from inyoka.utils.confirm import call_confirm, Expired
from inyoka.utils.pagination import URLPagination
from inyoka.utils.sortable import Sortable
from inyoka.portal.forms import get_profile_form
from inyoka.wiki.models import Revision as WikiRevision
from inyoka.forum.models import Question as ForumQuestion
from inyoka.news.models import Article as NewsArticle, Comment as NewsComment


def context_modifier(request, context):
    context.update(
        active='portal'
    )


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
        Rule('/groups/', endpoint='groups'),
        Rule('/group/<name>/', endpoint='group'),
    ]

    @view
    @templated('portal/profile_edit.html', modifier=context_modifier)
    def profile_edit(self, request):
        profile = UserProfile.query.filter_by(user_id=request.user.id).first()
        form = get_profile_form()(profile=profile)

        if request.method == 'POST' and form.validate(request.form):
            form.save()
            request.flash(_(u'Your profile was saved successfully'), True)

        return {'form':form.as_widget()}

    @view
    @templated('portal/index.html', modifier=context_modifier)
    def index(self, request):
        #TODO: get popular contents sorted by popularity, see
        #      :func:`inyoka.forum.models.Question.popularity` for example.
        items = []
        for model, column in ((WikiRevision, WikiRevision.change_date),
                      (ForumQuestion, ForumQuestion.date_active),
                      (NewsArticle, NewsArticle.updated),
                      (NewsComment, NewsComment.pub_date)):
            app = model.__tablename__.split('_', 1)[0].lower()
            value = [(app, obj) for obj in
                     model.query.order_by(column.desc()).limit(2).all()]
            items.extend(value)
        cloud, more = Tag.query.get_cloud()
        return {
            'introduction': True,
            'tag_cloud': cloud,
            'more_tags': more,
            'latest_content': items
        }

    @view
    @templated('portal/users.html', modifier=context_modifier)
    def users(self, request, page=1):
        query = User.query.options(db.joinedload('profile'))
        sortable = Sortable(query, 'id', request)
        pagination = URLPagination(sortable.get_sorted(), page)
        return {
            'users': pagination.query,
            'pagination': pagination,
            'table': sortable
        }

    @view
    @templated('portal/groups.html', modifier=context_modifier)
    def groups(self, request, page=1):
        sortable = Sortable(Group.query, 'id', request)
        pagination = URLPagination(sortable.get_sorted(), page)
        return {
            'groups': [group for group in pagination.query if group.parents],
            'pagination': pagination,
            'table': sortable
        }

    @view
    @templated('portal/group.html', modifier=context_modifier)
    def group(self, request, name, page=1):
        group = Group.query.filter_by(name=name).one()
        pagination = URLPagination(group.users, page)
        return {
            'group': group,
            'users': pagination.query,
            'pagination': pagination
        }

    @view
    @templated('portal/profile.html', modifier=context_modifier)
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
    @templated('portal/login.html', modifier=context_modifier)
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
