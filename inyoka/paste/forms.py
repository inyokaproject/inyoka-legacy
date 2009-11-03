#-*- coding: utf-8 -*-
"""
    inyoka.paste.forms
    ~~~~~~~~~~~~~~~~~~

    Forms for the paste app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

from pygments.lexers import get_all_lexers
from inyoka.core import forms
from inyoka.i18n import _



def _get_pygments_lexers(add_empty=True):
    r = []
    if add_empty:
        r.append(('', ''),)
    for lexer in get_all_lexers():
        r.append((lexer[1][0], _(lexer[0])),)
    return r


class AddPasteForm(forms.Form):
    code = forms.TextField(u'Code', required=True, widget=forms.widgets.Textarea)
    language = forms.ChoiceField(u'Highlighting',
                                 choices=list(_get_pygments_lexers()))
