# -*- coding: utf-8 -*-
"""
    inyoka.forum.forms
    ~~~~~~~~~~~~~~~~~~

    Formulars for the forum system.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.forms import Form, TextField, validators, widgets
from inyoka.core.forms.fields import QuerySelectField, AutocompleteField
from inyoka.core.forms.validators import ValidationError
from inyoka.i18n import lazy_gettext
from inyoka.forum.models import Forum, Tag


class AskQuestionForm(Form):

    title = TextField(lazy_gettext(u'Title'),
        [validators.length(max=160), validators.required()])
    text = TextField(lazy_gettext(u'Text'), [validators.required()],
                     widget=widgets.TextArea())
    tags = AutocompleteField(lazy_gettext(u'Tags'), get_label='name',
                        query_factory=lambda: Tag.query)


class AnswerQuestionForm(Form):

    text = TextField(lazy_gettext(u'Text'), [validators.required()],
                     widget=widgets.TextArea())


class EditForumForm(Form):

    name = TextField(lazy_gettext(u'Name'),
                     [validators.required(), validators.length(max=160)])
    slug = TextField(lazy_gettext(u'Slug'),
                     [validators.required(), validators.length(max=160)])
    parent = QuerySelectField(lazy_gettext(u'Parent'), query_factory=lambda: Forum.query,
                              get_label='name', allow_blank=True)
    description = TextField(lazy_gettext(u'Description'), [validators.required()],
                            widget=widgets.TextArea())
    tags = AutocompleteField(lazy_gettext(u'Tags'), get_label='name',
                             query_factory=lambda: Tag.query,
                             validators=[validators.length(min=1)])

    def validate_parent(self, field):
        message = lazy_gettext(u"You can't choose the forum itself or one of its subforums as parent")
        forum = Forum.query.filter_by(slug=self.slug.data).first()
        forums = Forum.query.filter_by(slug=self.slug.data).subforums()
        if field.data in forums or field.data == forum:
            raise ValidationError(message)
