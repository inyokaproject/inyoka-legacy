# -*- coding: utf-8 -*-
"""
    inyoka.portal.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the portal app.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from xappy.highlight import Highlighter
from inyoka.core.api import IController, Rule, view, Response, \
    templated, href, redirect, _, login_required
from inyoka.core.auth import get_auth_system
from inyoka.core.auth.models import User, UserProfile, Group
from inyoka.core.http import allow_next_redirects
from inyoka.core.models import Tag
from inyoka.core.search import query
from inyoka.context import ctx
from inyoka.core.database import db
from inyoka.utils.confirm import call_confirm, Expired
from inyoka.utils.pagination import URLPagination, SearchPagination
from inyoka.utils.sortable import Sortable
from inyoka.utils.text import get_search_words
from inyoka.portal.forms import ProfileForm, SearchForm, DeactivateProfileForm,\
    get_change_password_form
from inyoka.portal.api import ILatestContentProvider, ITaggableContentProvider


hl = Highlighter(ctx.cfg['language'])


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
        Rule('/groups/', endpoint='groups'),
        Rule('/group/<name>/', endpoint='group'),
        Rule('/tag/<slug>/', endpoint='tag'),
        Rule('/search/', endpoint='search'),
    ]

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
        user = User.query.options(db.joinedload(User.profile)).get(username)
        return {
            'user': user,
        }

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
            ret = _(u'Key not found. Maybe it has already been used?'), False
        except Expired:
            ret = _(u'The supplied key is not valid anymore.'), False

        if isinstance(ret, tuple) and len(ret) == 2:
            return Response(u'%s: %s' % (['success', 'fail'][not ret[1]],
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

    @view
    @templated('portal/search.html', modifier=context_modifier)
    def search(self, request):
        form = SearchForm(request.args)

        if 'q' in request.args and form.validate():
            d = form.data
            page, q = d['page'], d['q']

            # TODO: This is done by a celery task. As we have to wait for the
            #       result, the server process may be idle for some time. Maybe
            #       it would be better to send a temporary page and check
            #       dynamically via ajax whether the result has arrived.
            results, total, corrected = query('portal', q, author=d['author'],
                tag_list=[tag.name for tag in d['tags']],
                date_range=d['date_between'])

            pagination = SearchPagination(page, total, request.args)

            return {
                'results': results,
                'corrected': corrected,
                'form': form,
                'pagination': pagination,
                # XXX: Does it make sense to move this to a jinja template
                #      filter? I'm unsure as it's only used once.
                'highlight': lambda t, l: hl.makeSample(t, get_search_words(q),
                                maxlen=l, hl=('<strong>', '</strong>')),
            }
        return {
            'form': form,
        }


class UserCPExtension(IController):
    name = 'usercp'


class AlterProfileExtension(UserCPExtension):
    ext_name = _(u'Edit profile')
    ext_key = 'profile'

    url_rules = [
        Rule('/profile', endpoint='profile'),
    ]

    @login_required
    @view
    @templated('portal/usercp/profile.html', modifier=context_modifier)
    def profile(self, request):
        profile = UserProfile.query.filter_by(user_id=request.user.id).first()
        form = ProfileForm(request.form, profile=profile)

        if request.method == 'POST' and form.validate():
            form.save()
            request.flash(_(u'Your profile was saved successfully'), True)

        return {
            'form': form
        }


class PasswordExtension(UserCPExtension):
    ext_name = _(u'Change password')
    ext_key = 'password'

    url_rules = [
        Rule('/password', endpoint='password'),
    ]

    @view
    @login_required
    @templated('portal/usercp/password.html')
    def password(self, request):
        form = get_change_password_form(request)(request.form)

        if form.validate_on_submit():
            if not request.user.check_password(form.old_password.data):
                form.old_password.errors = [_(u'The password you entered '
                    u'doesn\'t match your old one.')]
            else:
                request.user.set_password(form.new_password.data)
                db.session.commit()
                request.flash(_(u'Your password was changed successfully'),
                      success=True)
                return redirect(href('usercp/index'))

        return {
            'random_pw': form.new_password.data,
            'form': form,
        }


class DeactivateExtension(UserCPExtension):
    ext_name = _(u'Deactivate Profile')
    ext_key = 'deactivate'

    url_rules = [
        Rule('/deactivate', endpoint='deactivate'),
    ]

    @login_required
    @view
    @templated('portal/usercp/deactivate.html', modifier=context_modifier)
    def deactivate(self, request):
        form = DeactivateProfileForm(request.form)

        if form.validate_on_submit():
            if not request.user.check_password(form.password.data):
                form.password.errors = [_(u'The password was not correct.')]
            else:
                user = request.user
                get_auth_system().logout(request)
                user.deactivate()
                db.session.commit()
                request.flash(_(u'Your profile was deactivated successfully'),
                     success=True)
                return redirect(href('portal/index'))

        return {
            'form': form
        }


class UserCPController(IController):
    name = 'usercp'
    url_rules = [
        Rule('/', endpoint='index'),
    ]

    def __init__(self, ctx):
        IController.__init__(self, ctx)
        self.extensions = dict((ext.ext_key, ext.ext_name)
            for ext in ctx.get_implementations(UserCPExtension))

    @view
    @login_required
    @templated('portal/usercp/index.html')
    def index(self, request):
        return {
            'extensions':   self.extensions,
        }
