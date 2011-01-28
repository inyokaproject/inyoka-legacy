# -*- coding: utf-8 -*-
"""
    inyoka.news.admin
    ~~~~~~~~~~~~~~~~~

    Admin providers for the news application.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.i18n import _
from inyoka.core.api import view, templated, redirect_to, db, Rule, render_template, \
    IController, login_required
from inyoka.core.forms.utils import model_to_dict, update_model
from inyoka.news.forms import EditArticleForm
from inyoka.news.models import Article


class NewsAdminProvider(IController):
    """The integration hook for the admin interface"""

    name = u'news'

    url_rules = [
        Rule('/new_article/', endpoint='article_edit', defaults={'slug': None}),
        Rule('/<slug>/edit/', endpoint='article_edit'),
        Rule('/<slug>/delete', endpoint='article_delete')
    ]

    @login_required
    @view('article_edit')
    @templated('news/admin/article_edit.html')
    def articles_edit(self, request, slug=None):
        new = slug is None
        if new:
            article, data = Article(), {'tags': []}
        else:
            article = Article.query.filter_by(slug=slug).one()
            data = model_to_dict(article, exclude=('slug'))

        form = EditArticleForm(request.form, **data)
        if 'delete' in request.form:
            return redirect_to('news/article_delete', slug=article.slug)
        elif form.validate_on_submit():
            article = update_model(article, form, ('pub_date', 'updated',
                'title', 'intro', 'text', 'public', 'tags',
                'author'))
            db.session.commit()
            request.flash(_(u'Updated article “%s”' % article.title), True)
            return redirect_to(article)
        return {
            'form': form,
            'article': article,
        }

    @login_required
    @view('article_delete')
    def articles_delete(self, request, slug):
        article = Article.query.filter_by(slug=slug).one()
        if 'cancel' in request.form:
            request.flash(_(u'Action canceled'))
        elif request.method in ('POST', 'PUT') and 'confirm' in request.form:
            db.session.delete(article)
            db.session.commit()
            request.flash(_(u'The article “%s” was deleted successfully.'
                          % article.title))
            return redirect_to('news/articles')
        else:
            request.flash(render_template('news/admin/article_delete.html', {
                'article': article
            }), html=True)
        return redirect_to(article, action='edit')
