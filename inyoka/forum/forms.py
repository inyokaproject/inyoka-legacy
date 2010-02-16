# -*- coding: utf-8 -*-
"""
    inyoka.forum.forms
    ~~~~~~~~~~~~~~~~~~

    Formulars for the forum system.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core import forms, auth
from inyoka.i18n import _
from inyoka.forum.models import Forum


class AskQuestionForm(forms.Form):

    title = forms.TextField(_(u'Title'), max_length=160, required=True)
    text = forms.TextField(_(u'Text'), widget=forms.widgets.Textarea,
        required=True)
    tags = forms.CommaSeparated(forms.TextField(), label=_(u'Tags'), sep=' ')


class AnswerQuestionForm(forms.Form):

    text = forms.TextField(_(u'Text'), widget=forms.widgets.Textarea,
        required=True)


class EditForumForm(forms.Form):

    name = forms.TextField(_(u'Name'), max_length=160)
    slug = forms.TextField(_(u'Slug'), max_length=160)
    description = forms.TextField(_(u'Description'), widget=forms.widgets.Textarea)
    tags = forms.CommaSeparated(forms.TextField(), label=_(u'Tags'), sep=' ')
