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
        Rule('/forum/add/', endpoint='forum')
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
        #entry = Entry.query.get(id)
        form = EditForumForm()
        
       # model_to_dict(entry,    exclude=('rendered_code', 'id', 'author_id')))
        if request.method == 'POST' and form.validate(request.form):
            #entry = update_model(entry, form,
            #    ('code', 'language', 'title', 'author', 'hidden'))
            tags = []
            for tagname in form.data['tags']:
                tag = Tag.query.filter_by(name=tagname).first()
                if not tag:
                    # XXX: Disable automatic tag creation
                    tag = Tag(tagname)
                    db.session.add(tag)
                tags.append(tag)
            forum = Forum(
                name=form.data['name'],
                slug=form.data['slug'],
                description=form.data['description'],
                tags=tags
            )
            db.session.add(forum)
            db.session.commit()
            return redirect_to('admin/forum/forum')

        return {
            'form': form.as_widget(),
        }
