# -*- coding: utf-8 -*-
"""
    inyoka.news.forms
    ~~~~~~~~~~~~~~~~~

    Formulars for the news system.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core import forms, auth
from inyoka.i18n import _
from inyoka.news.models import Tag


class EditArticleForm(forms.Form):

    title = forms.TextField(_(u'Title'), max_length=200, required=True)
    intro = forms.TextField(_(u'Intro'), widget=forms.widgets.Textarea,
                            required=True)
    text = forms.TextField(_(u'Text'), widget=forms.widgets.Textarea,
                           required=True)
    public = forms.BooleanField(_(u'Published'))
    tag = forms.ModelField(Tag, 'name', _(u'Tag'),
                           widget=forms.widgets.SelectBox, required=True)
    author = forms.ModelField(auth.User, 'username', _(u'Author'),
                              widget=forms.widgets.SelectBox, required=True)

    def __init__(self, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)
        # setup the possible choices for authors and tags
        authors = [u.username for u in auth.User.query.autoflush(False).all()]
        tags = [c.name for c in Tag.query.autoflush(False).all()]
        self.author.choices = authors
        self.tag.choices = tags


class EditCommentForm(forms.Form):
    text = forms.TextField(label=_(u'Text'), widget=forms.widgets.Textarea,
        help_text=_(u'To quote another comment use <em>@comment_number</em>. '
                    u'This is automatically used if you click “answer”.'))
