# -*- coding: utf-8 -*-
"""
    inyoka.paste.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the paste app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IController, Rule, view, Response, \
    templated, href, db, redirect_to, _
from inyoka.utils.pagination import URLPagination
from inyoka.admin.api import IAdminProvider
from inyoka.paste.forms import AddPasteForm, EditPasteForm
from inyoka.paste.models import Entry


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
    @templated('paste/index.html')
    def index(self, request):
        form = AddPasteForm()
        if request.method == 'POST' and form.validate(request.form):
            e = Entry(code=form.data['code'],
                      language=form.data['language'] or None,
                      title=form.data['title'],
                      author=request.user)
            db.session.add(e)
            db.session.commit()
            return redirect_to(e)

        recent_pastes = Entry.query.order_by(Entry.pub_date.desc())[:10]

        return {
            'recent_pastes': recent_pastes,
            'form': form.as_widget(),
        }

    @view('view')
    @templated('paste/view.html')
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
    @templated('paste/browse.html')
    def browse_pastes(self, request, page):
        query = Entry.query
        pagination = URLPagination(query, page)
        return {
            'pastes': pagination.query,
            'pagination': pagination.buttons(),
        }


class PasteAdminProvider(IAdminProvider):

    title = _(u'Paste')
    name = 'paste'
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
        form = EditPasteForm({
            'code': entry.code,
            'language': entry.language,
            'title': entry.title,
            'author': entry.author,
            'hidden': entry.hidden
        })
        if request.method == 'POST' and form.validate(request.form):
            entry.code = form.data['code']
            entry.language = form.data['language'] or None
            entry.title = form.data['title']
            entry.author = request.user
            entry.hidden = form.data['hidden']
            db.session.update(entry)
            db.session.commit()
            return redirect_to(entry)

        return {
            'form': form.as_widget(),
        }
