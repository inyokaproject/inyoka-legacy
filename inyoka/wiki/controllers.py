# -*- coding: utf-8 -*-
"""
    inyoka.paste.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the paste app.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

from inyoka.core.api import IController, Rule, view, templated, redirect_to, \
    ctx, db, _
from inyoka.core.exceptions import NotFound
from inyoka.wiki.forms import EditPageForm
from inyoka.wiki.models import Page, Revision, Text
from inyoka.wiki.utils import deurlify_page_name

class WikiController(IController):
    name = 'wiki'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/<path:page>/+edit', endpoint='edit'),
        Rule('/<path:page>/+history', endpoint='history'),
        Rule('/<path:page>/+<int:revision>', endpoint='show'),
        Rule('/<path:page>', endpoint='show'),
    ]

    @view
    def index(self, request):
        index = Page.query.get(ctx.cfg['wiki.index.name'])
        if index is None:
            raise NotFound()
        return redirect_to(index)


    @view
    @templated('wiki/show.html')
    def show(self, request, page, revision=None):
        page = Page.query.get(page)
        if page is None:
            raise NotFound()

        return {
            'page': page,
        }

    @view
    @templated('wiki/edit.html')
    def edit(self, request, page):
        page_name = page
        page = Page.query.get(page_name)
        if page is None:
            page = Page(name=page_name)
            initial = {}
        else:
            initial = {'text': page.current_revision.raw_text}


        form = EditPageForm(initial=initial)
        if request.method == 'POST' and form.validate(request.form):
            created = page.current_revision is None
            if not created and form['text'] == page.current_revision.raw_text:
                request.flash(_(u'Text didn\'t change!'))
                return redirect_to(page)

            r = Revision(
                page=page,
                raw_text=form['text'],
                change_comment=form['comment'],
                change_user=request.user,
            )
            db.session.add(r)
            db.session.commit()

            request.flash(_(u'The page has been saved'), True)
            return redirect_to(page)

        return {
            'page': page,
            'form': form.as_widget(),
        }

    @view
    @templated('wiki/history.html')
    def history(self, request, page):
        page = Page.query.get(page)
        if page is None:
            raise NotFound()

        revisions = page.revisions.order_by(Revision.id.desc()) \
                        .options(db.eagerload(Revision.change_user)).all()

        return {
            'page': page,
            'revisions': revisions,
        }
