# -*- coding: utf-8 -*-
"""
    inyoka.news.forms
    ~~~~~~~~~~~~~~~~~

    Formulars for the news system.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core import forms
from inyoka.i18n import _


class EditCategoryForm(forms.Form):
    name = forms.TextField(_(u'Name'), max_length=100)


#class AddPasteForm(forms.Form):
#    title = forms.TextField(_(u'Title (optional)'), max_length=50)
#    code = forms.TextField(_(u'Code'), required=True, widget=forms.widgets.Textarea)
#    language = forms.ChoiceField(_(u'Language'),
#                                 choices=list(_get_pygments_lexers()))
