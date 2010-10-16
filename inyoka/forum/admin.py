# -*- coding: utf-8 -*-
"""
    inyoka.forum.admin
    ~~~~~~~~~~~~~~~~~~

    All admin providers goes here.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import _, view, templated, db, Rule, redirect_to
from inyoka.core.forms.utils import model_to_dict, update_model
from inyoka.admin.api import IAdminProvider
from inyoka.forum.forms import EditForumForm
from inyoka.forum.models import Forum


class ForumAdminProvider(IAdminProvider):

    title = _(u'Forum')
    name = 'forum'
    index_endpoint = 'index'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/forum/add/', endpoint='forum'),
        Rule('/forum/edit/<int:id>/', endpoint='forum')
    ]

    @view
    @templated('forum/admin/index.html')
    def index(self, request):
        forums = Forum.query.all()
        return {
            'forums': forums
        }

    @view
    @templated('forum/admin/forum.html')
    def forum(self, request, id=None):
        if id:
            forum = Forum.query.get(id)
            initial = model_to_dict(forum)
        else:
            forum = None
            initial = {}

        form = EditForumForm(request.form, **initial)

        if form.validate_on_submit():
            if forum:
                forum = update_model(forum, form,
                    ('name', 'slug', 'parent', 'description', 'tags'))
            else:
                forum = Forum(
                    name=form.name.data,
                    slug=form.slug.data,
                    parent=form.parent.data,
                    description=form.description.data,
                    tags=form.tags.data
                )
            db.session.commit()
            return redirect_to('admin/forum/index')

        return {
            'forum': forum,
            'form': form,
        }
