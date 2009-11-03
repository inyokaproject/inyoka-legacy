#-*- coding: utf-8 -*-
"""
    inyoka.paste.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the paste app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import redirect
from inyoka.core.api import IController, Rule, register, register_service, \
    href, Response, templated, href, db
from inyoka.paste.forms import AddPasteForm
from inyoka.paste.models import Entry


class PasteController(IController):
    name = 'paste'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/paste/<int:id>/', endpoint='view_paste')
    ]


    @register('index')
    @templated('paste/index.html')
    def index(self, request):
        form = AddPasteForm()
        if request.method == 'POST' and form.validate(request.form):
            e = Entry(code=form.data['code'],
                      language=form.data['language'],
                      author_id=1)
            db.session.add(e)
            db.session.commit()
            return redirect(href(e))

        recent_pastes = Entry.query.order_by(Entry.pub_date.desc())[:10]

        return {
            'recent_pastes': recent_pastes,
            'form': form.as_widget(),
        }

    @register('view_paste')
    def view_paste(self, request, id):
        e = Entry.query.get(id)
        return Response(e.code, mimetype='text/plain')
