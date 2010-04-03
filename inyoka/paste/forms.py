# -*- coding: utf-8 -*-
"""
    inyoka.paste.forms
    ~~~~~~~~~~~~~~~~~~

    Forms for the paste app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

from operator import itemgetter
from pygments.lexers import get_all_lexers
from inyoka.core import forms
from inyoka.i18n import _


# Hell, we need a shorter list ;)
def _get_pygments_lexers(add_empty=True):
    r = []
    if add_empty:
        r.append(('', ''),)
    for lexer in get_all_lexers():
        r.append((lexer[1][0], _(lexer[0])),)
    r.sort(key=itemgetter(1))
    return r


class AddPasteForm(forms.Form):
    title = forms.TextField(_(u'Title (optional)'), max_length=50)
    text = forms.TextField(_(u'Text'), required=True, widget=forms.widgets.Textarea)
    language = forms.ChoiceField(_(u'Language'),
                                 choices=list(_get_pygments_lexers()))
    parent = forms.TextField(widget=forms.widgets.HiddenInput)


class EditPasteForm(AddPasteForm):
    hidden = forms.BooleanField(_(u'Hide Paste'))
