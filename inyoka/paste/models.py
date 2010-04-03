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
from functools import partial
from inyoka.core.api import _, db
from inyoka.core.mixins import RevisionedModelMixin, TextRendererMixin
from inyoka.core.auth.models import User
from inyoka.core.serializer import SerializableObject
from inyoka.paste.utils import generate_highlighted_udiff
from inyoka.utils.diff3 import prepare_udiff, generate_udiff
from inyoka.utils.highlight import highlight_text


class Entry(db.Model, SerializableObject, RevisionedModelMixin, TextRendererMixin):
    __tablename__ = 'paste_entry'

    # serializer properties
    object_type = 'paste.entry'
    public_fields = ('id', 'text', 'title', 'author', 'pub_date',
                     'hidden')

    #: The renderer that renders the text
    text_renderer = lambda s, v: highlight_text(v, s._language)

    #: Model columns
    id = db.Column(db.Integer, primary_key=True)
    _text = db.Column(db.Text, nullable=False)

    title =  db.Column(db.String(50), nullable=True)
    rendered_text = db.Column(db.Text, nullable=False)

    _language = db.Column('language', db.String(30))
    author_id = db.Column(db.ForeignKey(User.id), nullable=False)
    pub_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    hidden = db.Column(db.Boolean, default=False)

    author = db.relationship(User, lazy='joined')

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

    @property
    def display_title(self):
        if self.title:
            return self.title
        return _('Paste #%d') % self.id

    @property
    def has_tree(self):
        return bool(self.children) or bool(self.parent_id)

    def compare_to(self, other, column, context_lines=4, template=False):
        """Compare the mdoel with another revision.

        Special version to enable highlighting between files.

        :param other: The other model instance to compare with.
        :param column: A string what column to compare.
        :param context_lines: How many additional lines to show on the udiff.
        :param template: Either or not to prepare the udiff for templates use.
        """
        differ = generate_highlighted_udiff if template else generate_udiff

        generator = partial(differ,
            old=getattr(self, column, u''),
            new=getattr(other, column, u''),
            old_title=unicode(self),
            new_title=unicode(other),
            context_lines=context_lines)

        if template:
            udiff = generator(old_lang=self.language, new_lang=other.language)
        else:
            udiff = generator()

        if template:
            diff = prepare_udiff(udiff, True)
            return diff and diff[0] or None
        return udiff

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
