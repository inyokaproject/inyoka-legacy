# -*- coding: utf-8 -*-
"""
    inyoka.wiki.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the wiki app.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IController, Rule, view, templated, redirect_to, \
    ctx, db, _
from inyoka.core.http import Response
from inyoka.core.templating import render_template
from inyoka.core.exceptions import NotFound
from inyoka.wiki.forms import EditPageForm
from inyoka.wiki.models import Page, Revision, Text
from inyoka.wiki.utils import find_page, deurlify_page_name, urlify_page_name


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
        return redirect_to('wiki/show',
            page=urlify_page_name(ctx.cfg['wiki.index.name']))


    @view
    @templated('wiki/show.html')
    def show(self, request, page, revision=None):
        try:
            page = find_page(page, redirect_view='wiki/show',
                             redirect_params={'revision':revision})
        except NotFound:
            return Response(render_template('wiki/not_found.html', {
                'page':    page,
            }), status=404)

        if revision is not None:
            revision = Revision.query.get(revision)
            if revision is None or revision.page != page:
                raise NotFound(_(u'Invalid revision specified.'))
            if not revision.in_current_epoch: #TODO: allow for mods
                raise NotFound(_(u'Invalid revision specified.'))

        else:
            revision = page.current_revision

        return {
            'page': page,
            'revision': revision,
        }

    @view
    @templated('wiki/edit.html')
    def edit(self, request, page):
        try:
            page = find_page(url_name=page, redirect_view='wiki/edit')
        except NotFound:
            page = deurlify_page_name(page)
            url_name = urlify_page_name(page)
            if url_name != page:
                return redirect_to('wiki/edit', page=url_name)
            initial = {}
        else:
            initial = {'text': page.current_revision.raw_text}


        form = EditPageForm(request.form, **initial)
        if request.method == 'POST' and form.validate():
            page = Page(page)
            created = page.current_revision is None
            if not created and form.text.data == page.current_revision.raw_text:
                request.flash(_(u"Text didn't change."))
                return redirect_to(page)

            r = Revision(
                page=page,
                raw_text=form.text.data,
                change_comment=form.comment.data,
                change_user=request.user,
                epoch=1, #TODO: we definitely need a Page.edit method.
            )
            db.session.commit()

            request.flash(_(u'The page has been saved.'), True)
            return redirect_to(page)

        return {
            'page': page,
            'form': form,
        }

    @view
    @templated('wiki/history.html')
    def history(self, request, page):
        page = find_page(url_name=page, redirect_view='wiki/history')

        revisions = page.revisions.order_by(Revision.id.desc()) \
                        .options(db.joinedload(Revision.change_user)).all()

        return {
            'page': page,
            'revisions': revisions,
        }
