# -*- coding: utf-8 -*-
"""
    inyoka.paste.forms
    ~~~~~~~~~~~~~~~~~~

    Forms for the paste app.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from operator import itemgetter
from pygments.lexers import get_all_lexers
from inyoka.core.forms import Form, TextField, SelectField, BooleanField, \
    validators, widgets, HiddenIntegerField
from inyoka.i18n import _


# Hell, we need a shorter list ;)
def _get_pygments_lexers(add_empty=True):
    r = []
    if add_empty:
        r.append((u'', u''),)
    for lexer in get_all_lexers():
        r.append((lexer[1][0], _(lexer[0])),)
    r.sort(key=itemgetter(1))
    return r


class AddPasteForm(Form):
    title = TextField(_(u'Title (optional)'), [validators.length(max=50)])
    text = TextField(_(u'Text'), [validators.required()],
                     widget=widgets.TextArea())
    language = SelectField(_(u'Language'), choices=_get_pygments_lexers())
    parent = HiddenIntegerField()


class EditPasteForm(AddPasteForm):
    hidden = BooleanField(_(u'Hide Paste'))
