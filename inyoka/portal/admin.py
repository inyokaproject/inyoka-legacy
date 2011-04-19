# -*- coding: utf-8 -*-
"""
    inyoka.portal.admin
    ~~~~~~~~~~~~~~~~~~~

    Admin controllers for our core framework.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.i18n import _
from inyoka.core.api import db, view, templated, redirect_to, Rule, render_template, IController, href
from inyoka.core.models import Tag
from inyoka.core.forms.utils import model_to_dict, update_model
from inyoka.portal.forms import EditTagForm
from inyoka.utils import confirm_action


class PortalAdminController(IController):
    name = 'portal'

    url_rules = [
        Rule('/tag/new/', defaults={'slug': None},
             endpoint='tag_edit'),
        Rule('/tag/<slug>/edit', endpoint='tag_edit'),
        Rule('/tag/<slug>/delete', endpoint='tag_delete'),
    ]

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
            return redirect_to('portal/tag_delete', slug=tag.slug)
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
        message = _(u'Do you really want to delete this tag?')
        tag = Tag.query.filter_by(slug=slug).one()
        if confirm_action(request, message, 'portal/tag_delete', slug=slug):
            db.session.delete(tag)
            db.session.commit()
            request.flash(_(u'The tag “%s” was deleted successfully.' %
                            tag.name))
            return redirect_to('portal/tags')
        return redirect_to(tag)
