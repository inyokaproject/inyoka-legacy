# -*- coding: utf-8 -*-
"""
    inyoka.forum.admin
    ~~~~~~~~~~~~~~~~~~

    All admin providers goes here.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import _, view, templated, db, Rule, redirect_to, Response
from inyoka.core.forms.utils import model_to_dict, update_model
from inyoka.admin.api import IAdminProvider
from inyoka.forum.forms import EditForumForm
from inyoka.forum.models import Forum, Tag


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
            form = EditForumForm(model_to_dict(forum))
        else:
            forum = None
            form = EditForumForm()
        
        if request.method == 'POST' and form.validate(request.form):
            if forum:
                forum = update_model(forum, form, ('name', 'slug',
                            'parent', 'description', 'tags'))
            else:
                forum = Forum(
                    name=form.data['name'],
                    slug=form.data['slug'],
                    parent=form.data['parent'],
                    description=form.data['description'],
                    tags=form.data['tags']
                )
                db.session.add(forum)
            db.session.commit()
            return redirect_to('admin/forum/index')

        return {
            'form': form.as_widget(),
        }
