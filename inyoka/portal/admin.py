# -*- coding: utf-8 -*-
"""
    inyoka.portal.admin
    ~~~~~~~~~~~~~~~~~~~

    Admin controllers for our core framework.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.i18n import _
from inyoka.core.api import db, view, templated, redirect, redirect_to, db, \
    Rule, render_template
from inyoka.core.models import Tag
from inyoka.core.forms.utils import model_to_dict, update_model
from inyoka.admin.api import IAdminProvider
from inyoka.portal.forms import EditTagForm


class PortalAdminController(IAdminProvider):
    name = u'portal'
    title = _(u'Portal')

    index_endpoint = 'index'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/tags/', endpoint='tags'),
        Rule('/tags/new/', defaults={'slug': None},
             endpoint='tag_edit'),
        Rule('/tags/<slug>/', endpoint='tag_edit'),
        Rule('/tags/<slug>/delete', endpoint='tag_delete'),
    ]

    @view('index')
    @templated('portal/admin/index.html')
    def index(self, request):
        return {}

    @view('tags')
    @templated('portal/admin/tags.html')
    def tags(self, request):
        tags = Tag.query.all()
        return {
            'tags': tags
        }

    @view('tag_edit')
    @templated('portal/admin/tag_edit.html')
    def tags_edit(self, request, slug=None):
        new = slug is None
        if new:
            tag, data = Tag(), {}
        else:
            tag = Tag.query.filter_by(slug=slug).one()
            data = model_to_dict(tag, exclude=('slug'))

        form = EditTagForm(data)
        if 'delete' in request.form:
            return redirect_to('admin/portal/tag_delete', slug=tag.slug)
        elif request.method == 'POST' and form.validate(request.form):
            tag = update_model(tag, form, ('name'))
            db.session.commit()
            if new:
                request.flash(_(u'Created tag “%s”' % tag.name), True)
            else:
                request.flash(_(u'Updated tag “%s”' % tag.name), True)
        return {
            'form': form.as_widget(),
            'tag': tag,
        }

    @view('tag_delete')
    def tags_delete(self, request, slug):
        tag = Tag.query.filter_by(slug=slug).one()
        if 'cancel' in request.form:
            flash(_(u'Action canceled'))
        elif request.method == 'POST' and 'confirm' in request.form:
            db.session.delete(tag)
            db.session.commit()
            request.flash(_(u'The tag “%s” was deleted successfully.'
                          % tag.name))
            return redirect_to('admin/news/tags')
        else:
            request.flash(render_template('portal/admin/tag_delete.html', {
                'tag': tag
            }))
        return redirect_to(tag, action='edit')
