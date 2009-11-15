#-*- coding: utf-8 -*-
"""
    inyoka.paste.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the paste app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug.exceptions import NotFound
from inyoka.core.api import IController, Rule, register, Response, \
    templated, href, db, redirect
from inyoka.paste.forms import AddPasteForm
from inyoka.paste.models import Entry


class PasteController(IController):
    name = 'paste'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/paste/<int:id>/', endpoint='view'),
        Rule('/raw/<int:id>/', endpoint='raw'),
        Rule('/browse/', endpoint='browse'),
    ]


    @register()
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
            return redirect(href(e))

        recent_pastes = Entry.query.order_by(Entry.pub_date.desc())[:10]
        print recent_pastes

        return {
            'recent_pastes': recent_pastes,
            'form': form.as_widget(),
        }

    @register('view')
    @templated('paste/view.html')
    def view_paste(self, request, id):
        e = Entry.query.get(id)
        if e is None:
            raise NotFound
        return {
            'paste': e,
        }

    @register('raw')
    def raw_paste(self, request, id):
        e = Entry.query.get(id)
        if e is None:
            raise NotFound
        return Response(e.code, mimetype='text/plain')

    @register('browse')
    @templated('paste/browse.html')
    def browse_pastes(self, request):
        pastes = Entry.query.all()
        return {
            'pastes': pastes,
        }
