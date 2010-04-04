# -*- coding: utf-8 -*-
"""
    inyoka.wiki.models
    ~~~~~~~~~~~~~~~~~~

    Models for the wiki.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import datetime
from operator import attrgetter
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import synonym
from inyoka.core.api import db
from inyoka.core.mixins import TextRendererMixin
from inyoka.core.auth.models import User
from inyoka.utils.html import escape
from inyoka.wiki.utils import deurlify_page_name, urlify_page_name


class PageQuery(db.Query):
    def get(self, pk):
        if isinstance(pk, basestring):
            try:
                #TODO: select case-insensitively
                return Page.query.filter_by(name=deurlify_page_name(pk)).one()
            except db.NoResultFound:
                return
        return super(PageQuery, self).get(pk)


class PageMapperExtension(db.MapperExtension):
    """
    * Updates current_revision.
    """
    def after_insert(self, mapper, connection, instance):
        instance._update_current_revision()

    def after_update(self, mapper, connection, instance):
        instance._update_current_revision()


class Page(db.Model):
    __tablename__ = 'wiki_page'
    query = db.session.query_property(PageQuery)
    __mapper_args__ = {
        'extension': PageMapperExtension(),
    }

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), index=True, nullable=False)
    current_revision_id = db.Column(db.Integer,
        db.ForeignKey('wiki_revision.id', name='current_revision_id',
                      use_alter=True)) # avoid circular dependency

    current_revision = db.relation('Revision',
        primaryjoin='Page.current_revision_id == Revision.id')

    def __init__(self, name):
        self.name = deurlify_page_name(name)
        db.session.add(self)

    def __repr__(self):
        return '<Page %r>' % self.name

    @property
    def url_name(self):
        return urlify_page_name(self.name)

    def get_url_values(self, action='show', revision=None):
        if action == 'show':
            return 'wiki/show', {'page': self.url_name, 'revision': revision}
        elif action in ('history', 'edit'):
            return 'wiki/%s' % action, {'page': self.url_name}

    def _update_current_revision(self):
        """
        Set ``current_revision`` to the newest revision for this page.
        """
        self.current_revision_id = db.session.execute(
                db.select([db.func.max(Revision.id)], Revision.page_id == self.id)
            ).scalar()


class Text(db.Model, TextRendererMixin):
    __tablename__ = 'wiki_text'

    id = db.Column(db.Integer, primary_key=True)
    _text = db.Column('text', db.Text, nullable=False)
    rendered_text = db.Column('rendered_text', db.Text)

    def __repr__(self):
        return '<Text #%r>' % self.id


def _create_text(value):
    return Text(text=value)


class Revision(db.Model):
    __tablename__ = 'wiki_revision'

    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.ForeignKey(Page.id), nullable=False)
    change_user_id = db.Column(db.ForeignKey(User.id), nullable=False)
    change_date = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    change_comment = db.Column(db.String(512))
    text_id = db.Column(db.ForeignKey(Text.id))

    page = db.relation(Page, primaryjoin='Revision.page_id == Page.id',
                       backref=db.backref('revisions', lazy='dynamic'))
    text = db.relation(Text)
    change_user = db.relation(User)

    raw_text = association_proxy('text', 'text', creator=_create_text)
    rendered_text = association_proxy('text', 'rendered_text')
    #TODO: rendered_text should be readonly.

    def __repr__(self):
        pn = repr(self.page.name) if self.page else None
        return '<Revision #%r %s>' % (self.id, pn)

    def __unicode__(self):
        return self.page.name

    def get_url_values(self, action='show', revision=None):
        if action == 'show':
            return 'wiki/show', {'page': self.page.url_name, 'revision': revision}


class WikiSchemaController(db.ISchemaController):
    models = [Page, Revision, Text]
