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
from inyoka.paste.forms import EditPasteForm
from inyoka.paste.models import Entry


class ForumAdminProvider(IAdminProvider):

    title = _(u'Forum')
    name = 'Forum'
    index_endpoint = 'index'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/edit/<int:id>/', endpoint='edit')
    ]

    @view
    def index(self, request):
        return Response('Paste Admin Index')

    @view
    @templated('paste/admin/edit.html')
    def edit(self, request, id):
        entry = Entry.query.get(id)
        form = EditPasteForm(model_to_dict(entry,
            exclude=('rendered_code', 'id', 'author_id')
        ))
        if request.method == 'POST' and form.validate(request.form):
            entry = update_model(entry, form,
                ('code', 'language', 'title', 'author', 'hidden'))
            db.session.update(entry)
            db.session.commit()
            return redirect_to(entry)

        return {
            'form': form.as_widget(),
        }
