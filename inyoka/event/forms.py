# -*- coding: utf-8 -*-
"""
    inyoka.event.forms
    ~~~~~~~~~~~~~~~~~~

    Forms for the event app.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from operator import itemgetter
from inyoka.core.forms import Form, AutocompleteField, TextField, \
    DateTimeField, BooleanField, validators, widgets
from inyoka.i18n import _
from inyoka.news.models import Tag


class AddEventForm(Form):
    title = TextField(_(u'Title'), [validators.Length(max=100),
                     validators.Required()])
    text = TextField(_(u'Text'), [validators.Required()],
                     widget=widgets.TextArea())
    start = DateTimeField(_(u'Start'), [validators.Required()])
    end = DateTimeField(_(u'End'), [validators.Required()])
    tags = AutocompleteField(_(u'Tags'), get_label='name',
                             query_factory=lambda: Tag.query.autoflush(False))
    discussion_question = BooleanField(_(u'Create topic for discussion'))
    info_question = BooleanField(_(u'Create topic for further information'))
