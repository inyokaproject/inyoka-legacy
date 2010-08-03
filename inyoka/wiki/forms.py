# -*- coding: utf-8 -*-
"""
    inyoka.wiki.forms
    ~~~~~~~~~~~~~~~~~

    Forms for the wiki app.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.forms import Form, widgets, validators, TextField, FileField, \
    BooleanField
from inyoka.i18n import _


class EditPageForm(Form):
    text = TextField(_(u'Text'), [validators.Required()], widget=widgets.TextArea())
    comment = TextField(_(u'Edit comment'), [validators.Length(max=512)])


class AttachmentForm(Form):
    file = FileField(_(u'File'))
    rename_to = TextField(_(u'Rename to'), [validators.is_valid_attachment_name()])
    description = TextField(_(u'Description'), widget=widgets.TextArea())
    comment = TextField(_(u'Edit comment'), [validators.Length(max=512)])
    overwrite = BooleanField(_(u'Overwrite existing attachment with the same '
        u'name'))
