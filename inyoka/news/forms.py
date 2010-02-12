# -*- coding: utf-8 -*-
"""
    inyoka.news.forms
    ~~~~~~~~~~~~~~~~~

    Formulars for the news system.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core import forms, auth
from inyoka.i18n import _
from inyoka.news.models import Category


class EditCategoryForm(forms.Form):
    name = forms.TextField(_(u'Name'), max_length=100)


class EditArticleForm(forms.Form):

    title = forms.TextField(_(u'Title'), max_length=200)
    intro = forms.TextField(_(u'Intro'), widget=forms.widgets.Textarea)
    text = forms.TextField(_(u'Text'), widget=forms.widgets.Textarea)
    public = forms.BooleanField(_(u'Published'))
    category = forms.ModelField(Category, 'name', _(u'Category'),
                                widget=forms.widgets.SelectBox)
    author = forms.ModelField(auth.User, 'username', _(u'Author'),
                              widget=forms.widgets.SelectBox)

    def __init__(self, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)
        # setup the possible choices for authors and categories
        self.author.choices = [u.username for u in auth.User.query.autoflush(False).all()]
        self.category.choices = [c.name for c in Category.query.autoflush(False).all()]
