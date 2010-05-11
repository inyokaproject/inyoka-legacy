# -*- coding: utf-8 -*-
"""
    inyoka.wiki.forms
    ~~~~~~~~~~~~~~~~~~

    Forms for the wiki app.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from wtforms import TextField, widgets, validators
from inyoka.i18n import _
from inyoka.utils.forms import Form


class EditPageForm(Form):
    text = TextField(_(u'Text'), [validators.Required()], widget=widgets.TextArea())
    comment = TextField(_(u'Edit comment'), [validators.Length(512)])
