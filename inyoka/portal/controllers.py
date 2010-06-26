# -*- coding: utf-8 -*-
"""
    inyoka.portal.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the portal app.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IController, Rule, view, Response, \
    templated, _
from inyoka.core.auth import get_auth_system, login_required
from inyoka.core.auth.models import User, UserProfile, IUserProfileExtender, \
    Group
from inyoka.core.http import allow_next_redirects
from inyoka.core.models import Tag
from inyoka.context import ctx
from inyoka.core.database import db
from inyoka.utils.confirm import call_confirm, Expired
from inyoka.utils.pagination import URLPagination
from inyoka.utils.sortable import Sortable
from inyoka.portal.forms import get_profile_form
from inyoka.portal.api import ILatestContentProvider, ITaggableContentProvider


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
        Rule('/users/<int:page>/', endpoint='users'),
        Rule('/user/<username>/', endpoint='profile'),
        Rule('/usercp/profile/', endpoint='profile_edit'),
        Rule('/groups/', endpoint='groups'),
        Rule('/group/<name>/', endpoint='group'),
        Rule('/tag/<slug>/', endpoint='tag'),
    ]

    @login_required
    @view
    @templated('portal/profile_edit.html', modifier=context_modifier)
    def profile_edit(self, request):
        profile = UserProfile.query.filter_by(user_id=request.user.id).first()
        form = get_profile_form()(request.form, profile=profile)

        if request.method == 'POST' and form.validate():
            form.save()
            request.flash(_(u'Your profile was saved successfully'), True)

        return {'form': form}

    @view
    @templated('portal/index.html', modifier=context_modifier)
    def index(self, request):
        contents = ILatestContentProvider.get_cached_content(2)
        cloud, more = Tag.query.public().get_cloud()
        return {
            'tag_cloud': cloud,
            'more_tags': more,
            'latest_content': contents,
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
    @allow_next_redirects('portal/index')
    def login(self, request):
        return get_auth_system().login(request)

    @view
    @allow_next_redirects('portal/index')
    def logout(self, request):
        return get_auth_system().logout(request)

    @view
    @allow_next_redirects('portal/index')
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

    @view
    @templated('portal/tag.html', modifier=context_modifier)
    def tag(self, request, slug):
        tag = Tag.query.filter_by(slug=slug).one()
        providers = ctx.get_implementations(ITaggableContentProvider, instances=True)
        content = []
        for provider in providers:
            content.append({
                'item_list': provider.get_taggable_content(tag).all(),
                'list_class': provider.type,
                'name': provider.name
            })

        return {
            'tag': tag,
            'content': content,
        }


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
