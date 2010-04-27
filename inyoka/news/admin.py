# -*- coding: utf-8 -*-
"""
    inyoka.news.admin
    ~~~~~~~~~~~~~~~~~

    Admin providers for the news application.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.i18n import _
from inyoka.core.api import view, templated, redirect, redirect_to, db, Rule, \
    render_template
from inyoka.core.forms.utils import model_to_dict, update_model
from inyoka.admin.api import IAdminProvider
from inyoka.news.forms import EditArticleForm
from inyoka.news.models import Article


class NewsAdminProvider(IAdminProvider):
    """The integration hook for the admin interface"""

    name = u'news'
    title = _(u'News')

    index_endpoint = 'index'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/articles/', endpoint='articles'),
        Rule('/articles/new/', defaults={'slug': None},
             endpoint='article_edit'),
        Rule('/articles/<slug>/', endpoint='article_edit'),
        Rule('/articles/<slug>/delete', endpoint='article_delete'),
    ]

    @view('index')
    @templated('news/admin/index.html')
    def index(self, request):
        return {}

    @view('articles')
    @templated('news/admin/articles.html')
    def articles(self, request):
        articles = Article.query.all()
        return {
            'articles': articles
        }

    @view('article_edit')
    @templated('news/admin/article_edit.html')
    def articles_edit(self, request, slug=None):
        new = slug is None
        if new:
            article, data = Article(), {}
        else:
            article = Article.query.filter_by(slug=slug).one()
            data = model_to_dict(article, exclude=('slug'))

        form = EditArticleForm(data)
        if 'delete' in request.form:
            return redirect_to('admin/news/article_delete', slug=article.slug)
        elif request.method == 'POST' and form.validate(request.form):
            article = update_model(article, form, ('pub_date', 'updated',
                'title', 'intro', 'text', 'public', 'tags',
                'author'))
            db.session.commit()
            request.flash(_(u'Updated article “%s”' % article.title), True)
        return {
            'form': form.as_widget(),
            'article': article,
        }

    @view('article_delete')
    def articles_delete(self, request, slug):
        article = Article.query.filter_by(slug=slug).one()
        if 'cancel' in request.form:
            flash(_(u'Action canceled'))
        elif request.method == 'POST' and 'confirm' in request.form:
            db.session.delete(article)
            db.session.commit()
            request.flash(_(u'The article “%s” was deleted successfully.'
                          % article.title))
            return redirect_to('admin/news/articles')
        else:
            request.flash(render_template('news/admin/article_delete.html', {
                'article': article
            }))
        return redirect_to(article, action='edit')
