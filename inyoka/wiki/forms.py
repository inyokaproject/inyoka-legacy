# -*- coding: utf-8 -*-
"""
    inyoka.wiki.forms
    ~~~~~~~~~~~~~~~~~~

    Forms for the wiki app.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core import forms
from inyoka.i18n import _

class EditPageForm(forms.Form):
    text = forms.TextField(_(u'Text'), required=True,
                           widget=forms.widgets.Textarea)
    comment = forms.TextField(_(u'Edit comment'), max_length=512)
