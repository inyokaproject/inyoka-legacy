# -*- coding: utf-8 -*-
"""
    inyoka.paste.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the paste app.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
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
        Rule('/compare/', endpoint='compare_paste'),
        Rule('/compare/<int:new_id>/<int:old_id>/', endpoint='compare_paste'),
        Rule('/unidiff/<int:new_id>/<int:old_id>/', endpoint='unidiff_paste'),
        Rule('/tree/<int:id>/', endpoint='show_tree'),
    ]

    @view
    @templated('paste/index.html', modifier=context_modifier)
    def index(self, request):
        form = AddPasteForm(request.form)
        if request.method == 'POST' and form.validate():
            e = Entry(text=form.text.data,
                      language=form.language.data or None,
                      title=form.title.data,
                      author=request.user,
                      parent_id=form.parent.data)
            db.session.commit()
            return redirect_to(e)
        else:
            parent_id = request.args.get('reply_to', None)
            if parent_id is not None:
                parent = Entry.query.get(int(parent_id))
                form = AddPasteForm(**{
                    'title': parent.title,
                    'language': parent.language,
                    'text': parent.text,
                    'parent': parent.id
                })

        return {
            'form': form,
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
        return Response(e.text, mimetype='text/plain')

    @view('browse')
    @templated('paste/browse.html', modifier=context_modifier)
    def browse_pastes(self, request, page):
        query = Entry.query
        pagination = URLPagination(query, page=page)
        return {
            'pastes': pagination.query,
            'pagination': pagination,
        }

    @view('show_tree')
    @templated('paste/paste_tree.html', modifier=context_modifier)
    def show_tree(self, request, id):
        """Display the tree of some related pastes."""
        paste = Entry.resolve_root(id)
        if paste is None:
            raise NotFound()
        return {
            'paste': paste,
            'current': id
        }

    @view('compare_paste')
    @templated('paste/compare_paste.html', modifier=context_modifier)
    def compare_paste(self, request, new_id=None, old_id=None):
        """Render a diff view for two pastes."""
        old = Entry.query.get(old_id)
        new = Entry.query.get(new_id)
        if old is None or new is None:
            raise NotFound()

        return {
            'old': old,
            'new': new,
            'diff': old.compare_to(new, 'text', template=True)
        }

    @view('unidiff_paste')
    def unidiff_paste(self, request, new_id=None, old_id=None):
        """Render an udiff for the two pastes."""
        old = Entry.query.get(old_id)
        new = Entry.query.get(new_id)

        if old is None or new is None:
            raise NotFound()

        return Response(old.compare_to(new, 'text'), mimetype='text/plain')
