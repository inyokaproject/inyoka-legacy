# -*- coding: utf-8 -*-
"""
    inyoka.news.forms
    ~~~~~~~~~~~~~~~~~

    Formulars for the news system.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from wtforms import Form, TextField, BooleanField, widgets, validators
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from inyoka.core.auth.models import User
from inyoka.i18n import _
from inyoka.news.models import Tag


class EditArticleForm(Form):

    title = TextField(_(u'Title'), [validators.Required(), validators.Length(max=200)])
    intro = TextField(_(u'Intro'), [validators.Required()], widget=widgets.TextArea())
    text = TextField(_(u'Text'), [validators.Required()], widget=widgets.TextArea())
    public = BooleanField(_(u'Published'))
    tags = QuerySelectMultipleField(_(u'Tags'), Tag.query.autoflush(False), get_label='name')
    author = QuerySelectField(_(u'Author'), [validators.Required],
                             User.query.autoflush(False), widget=widgets.Select())


class EditCommentForm(Form):
    text = TextField(_(u'Text'), widget=widgets.TextArea(),
        description=_(u'To quote another comment use <em>@comment_number</em>. '
                      u'This is automatically used if you click “answer”.'))
