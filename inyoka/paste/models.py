# -*- coding: utf-8 -*-
"""
    inyoka.paste.models
    ~~~~~~~~~~~~~~~~~~~

    Models for the paste app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import datetime
from operator import attrgetter
from inyoka.core.api import _, db
from inyoka.core.mixins import RevisionedModelMixin, TextRendererMixin
from inyoka.core.auth.models import User
from inyoka.core.serializer import SerializableObject
from inyoka.utils.highlight import highlight_code


class Entry(db.Model, SerializableObject, RevisionedModelMixin, TextRendererMixin):
    __tablename__ = 'paste_entry'

    # serializer properties
    object_type = 'paste.entry'
    public_fields = ('id', 'code', 'title', 'author', 'pub_date',
                     'hidden')

    #: The renderer that renders the code
    text_renderer = lambda s, v: highlight_code(v, s._language)

    #: Model columns
    id = db.Column(db.Integer, primary_key=True)
    _text = db.Column('code', db.Text, nullable=False)
    code = db.synonym('text')

    title =  db.Column(db.String(50), nullable=True)
    rendered_text = db.Column(db.Text, nullable=False)
    rendered_code = db.synonym('rendered_text')

    _language = db.Column('language', db.String(30))
    author_id = db.Column(db.ForeignKey(User.id), nullable=False)
    pub_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    hidden = db.Column(db.Boolean, default=False)

    author = db.relationship(User, lazy=False)

    # revision model implementation
    parent_id = db.Column(db.Integer, db.ForeignKey(id), nullable=True)
    children = db.relationship('Entry', cascade='all',
        primaryjoin=parent_id == id,
        backref=db.backref('parent', remote_side=[id]))

    def get_url_values(self, action='view'):
        if action == 'reply':
            return 'paste/index', {'reply_to': self.id}
        values = {
            'view': 'paste/view',
            'raw':  'paste/raw',
            'show_tree': 'paste/show_tree',
            'edit': 'admin/paste/edit',
        }
        return values[action], {'id': self.id}

    def _set_language(self, language):
        changed = language != self._language
        self._language = language
        if changed and not self._rendered:
            self._render()
    language = db.synonym('_language', descriptor=property(
        attrgetter('_language'), _set_language))
    code = db.synonym('text')

    @property
    def display_title(self):
        if self.title:
            return self.title
        return _('Paste #%d') % self.id

    @property
    def has_tree(self):
        return bool(self.children) or bool(self.parent_id)

    def __unicode__(self):
        return self.display_title

    def __repr__(self):
        if self.title:
            s = repr(self.title)
        else:
            s = '#%s' % self.id if self.id else '[no id]'
        u = self.author.username
        return '<Entry %s by %s>' % (s, u)


class PasteSchemaController(db.ISchemaController):
    models = [Entry]
