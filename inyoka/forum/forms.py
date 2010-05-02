# -*- coding: utf-8 -*-
"""
    inyoka.forum.forms
    ~~~~~~~~~~~~~~~~~~

    Formulars for the forum system.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from wtforms import Form, TextField, validators, widgets
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from inyoka.core.api import _, db
from inyoka.i18n import _, lazy_gettext
from inyoka.forum.models import Forum, Tag


class AskQuestionForm(Form):

    title = TextField(lazy_gettext(u'Title'),
        [validators.Length(max=160), validators.Required()])
    text = TextField(lazy_gettext(u'Text'), [validators.Required()],
                     widget=widgets.TextArea())
#    tags = forms.Autocomplete(forms.ModelField(Tag, 'name'),
#                              label=_(u'Tags'), sep=',', min_size=1)
    tags = QuerySelectMultipleField(lazy_gettext(u'Tags'), query_factory=lambda: Tag.query,
                                    get_label='name')


class AnswerQuestionForm(Form):

    text = TextField(lazy_gettext(u'Text'), [validators.Required()],
                     widget=widgets.TextArea())


class EditForumForm(Form):

    name = TextField(lazy_gettext(u'Name'),
                     [validators.Required(), validators.Length(max=160)])
    slug = TextField(lazy_gettext(u'Slug'),
                     [validators.Required(), validators.Length(max=160)])
    parent = QuerySelectField(lazy_gettext(u'Parent'), query_factory=lambda: Forum.query,
                              get_label='name')
    description = TextField(lazy_gettext(u'Description'), [validators.Required()],
                            widget=widgets.TextArea())
    tags = QuerySelectMultipleField(lazy_gettext(u'Tags'), query_factory=lambda: Tag.query,
                                    get_label='name')
