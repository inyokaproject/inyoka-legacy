# -*- coding: utf-8 -*-
"""
    inyoka.news.admin
    ~~~~~~~~~~~~~~~~~

    Admin providers for the news application.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.i18n import _
from inyoka.core.api import view, templated, redirect_to, db, Rule, Response
from inyoka.core.forms.utils import model_to_dict, update_model
from inyoka.admin.api import IAdminProvider
from inyoka.news.forms import EditCategoryForm
from inyoka.news.models import Category


class NewsAdminProvider(IAdminProvider):
    """The integration hook for the admin interface"""

    name = u'news'
    title = _(u'News')

    index_endpoint = 'index'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/categories/', endpoint='categories'),
        Rule('/categories/new/', defaults={'slug': None},
             endpoint='category_edit'),
        Rule('/categories/<slug>/', endpoint='category_edit')
    ]

    @view('index')
    @templated('news/admin/index.html')
    def index(self, request):
        return {}

    @view('categories')
    @templated('news/admin/categories.html')
    def categories(self, request):
        categories = Category.query.all()
        return {
            'categories': categories
        }

    @view('category_edit')
    @templated('news/admin/category_edit.html')
    def categories_edit(self, request, slug=None):
        new = slug is None
        if new:
            category, data = Category(), {}
        else:
            category = Category.query.filter_by(slug=slug).one()
            data = model_to_dict(category, exclude=('slug'))

        form = EditCategoryForm(data)
        if request.method == 'POST' and form.validate(request.form):
            category = update_model(category, form, ('name'))
            if new:
                db.session.add(category)
            else:
                db.session.update(category)
            db.session.commit()
            return redirect_to(category)
        return {
            'form': form.as_widget(),
            'category': category,
        }
