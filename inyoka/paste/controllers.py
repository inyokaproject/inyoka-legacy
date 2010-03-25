# -*- coding: utf-8 -*-
"""
    inyoka.paste.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the paste app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IController, Rule, view, Response, \
    templated, db, redirect_to
from inyoka.utils.pagination import URLPagination
from inyoka.paste.forms import AddPasteForm
from inyoka.paste.models import Entry


def context_modifier(request, context):
    context.update(
        active='paste'
    )


class PasteController(IController):
    name = 'paste'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/paste/<int:id>/', endpoint='view'),
        Rule('/raw/<int:id>/', endpoint='raw'),
        Rule('/browse/', defaults={'page': 1}, endpoint='browse'),
        Rule('/browse/<int:page>/', endpoint='browse'),
    ]

    @view
    @templated('paste/index.html', modifier=context_modifier)
    def index(self, request):
        form = AddPasteForm()
        if request.method == 'POST' and form.validate(request.form):
            e = Entry(code=form.data['code'],
                      language=form.data['language'] or None,
                      title=form.data['title'],
                      author=request.user)
            db.session.commit()
            return redirect_to(e)

        return {
            'recent_pastes': recent_pastes,
            'form': form.as_widget(),
        }

    @view('view')
    @templated('paste/view.html', modifier=context_modifier)
    def view_paste(self, request, id):
        e = Entry.query.get(id)
        return {
            'paste': e,
        }

    @view('raw')
    def raw_paste(self, request, id):
        e = Entry.query.get(id)
        return Response(e.code, mimetype='text/plain')

    @view('browse')
    @templated('paste/browse.html', modifier=context_modifier)
    def browse_pastes(self, request, page):
        query = Entry.query
        pagination = URLPagination(query, page=page)
        return {
            'pastes': pagination.get_objects(),
            'pagination': pagination,
        }
