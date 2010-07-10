# -*- coding: utf-8 -*-
"""
    inyoka.portal.admin
    ~~~~~~~~~~~~~~~~~~~

    Admin controllers for our core framework.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.i18n import _
from inyoka.core.api import db, view, templated, redirect_to, Rule, render_template
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
        cloud, more = Tag.query.public().get_cloud()
        if request.method in ('POST', 'PUT'):
            # the user choosed a tag by manually entered name
            name = request.form.get('tag')
            tag = Tag.query.filter_by(name=name).first()
            if tag is not None:
                return redirect_to('admin/portal/tag_edit', slug=tag.slug)
            request.flash(_(u'The tag “%s” does not exist'), False)

        return {
            'tag_cloud': cloud,
            'tag_names': [t['name'] for t in cloud]
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

        form = EditTagForm(request.form, **data)

        if 'delete' in request.form:
            return redirect_to('admin/portal/tag_delete', slug=tag.slug)
        elif form.validate_on_submit():
            tag = update_model(tag, form, ('name'))
            db.session.commit()
            if new:
                request.flash(_(u'Created tag “%s”' % tag.name), True)
            else:
                request.flash(_(u'Updated tag “%s”' % tag.name), True)

        return {
            'form': form,
            'tag': tag,
        }

    @view('tag_delete')
    def tags_delete(self, request, slug):
        tag = Tag.query.filter_by(slug=slug).one()
        if 'cancel' in request.form:
            request.flash(_(u'Action canceled'))
        elif 'confirm' in request.form and form.validate_on_submit():
            db.session.delete(tag)
            db.session.commit()
            request.flash(_(u'The tag “%s” was deleted successfully.'
                          % tag.name))
            return redirect_to('admin/portal/tags')
        else:
            request.flash(render_template('portal/admin/tag_delete.html', {
                'tag': tag
            }), html=True)
        return redirect_to(tag, action='edit')
