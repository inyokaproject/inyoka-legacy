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
from inyoka.portal.api import ILatestContentProvider


class WikiLatestContentProvider(ILatestContentProvider):

    type = 'wiki_revisions'
    cache_key = 'wiki/latest_revisions'

    def get_latest_content(self):
        return Revision.query.options(db.eagerload('page')) \
                       .order_by(Revision.change_date.desc())


class PageQuery(db.Query):
    def filter_name(self, name):
        return self.filter(db.func.lower(Page.name)==name.lower())

    def get(self, pk):
        if isinstance(pk, basestring):
            try:
                return Page.query.filter_name(pk).one()
            except db.NoResultFound:
                return
        return super(PageQuery, self).get(pk)


class Page(db.Model):
    __tablename__ = 'wiki_page'
    query = db.session.query_property(PageQuery)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), index=True, nullable=False)
    current_revision_id = db.Column(db.Integer,
        db.ForeignKey('wiki_revision.id', name='current_revision_id',
                      use_alter=True)) # avoid circular dependency
    current_epoch = db.Column(db.Integer, default=1, nullable=False)
    deleted = db.Column(db.Boolean, nullable=False, default=False)

    current_revision = db.relationship('Revision', post_update=True,
        primaryjoin='Page.current_revision_id == Revision.id')

    def __init__(self, name, **kwargs):
        self.name = name
        super(Page, self).__init__(**kwargs)

    def __repr__(self):
        return '<Page %r>' % self.name

    @property
    def url_name(self):
        return urlify_page_name(self.name)

    def get_url_values(self, action='show', revision=None):
        if action == 'show':
            return 'wiki/show', {
                'page': self.url_name,
                'revision': getattr(revision, 'id', revision)
            }
        elif action in ('history', 'edit'):
            return 'wiki/%s' % action, {'page': self.url_name}


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
    epoch = db.Column(db.Integer, nullable=False)

    _page = db.relationship(Page, primaryjoin='Revision.page_id == Page.id',
        backref=db.backref('all_revisions', lazy='dynamic'))
    text = db.relationship(Text)
    change_user = db.relationship(User)

    raw_text = association_proxy('text', 'text', creator=_create_text)
    rendered_text = association_proxy('text', 'rendered_text')

    def _set_page(self, page):
        if page is not None:
            page.current_revision = self
        self._page = page
    page = db.synonym('_page',
                      descriptor=property(attrgetter('_page'), _set_page))
    del _set_page

    def __repr__(self):
        pn = repr(self.page.name) if self.page else None
        return '<Revision #%r %s>' % (self.id, pn)

    def __unicode__(self):
        return self.page.name

    def get_url_values(self, action='show'):
        return 'wiki/show', {'page': self.page.url_name, 'revision': self.id}

    @property
    def in_current_epoch(self):
        return self.epoch == self.page.current_epoch


# doesn't work for whatever reason if defined inside the page object.
Page.revisions = db.relationship(Revision, lazy='dynamic',
    primaryjoin=db.and_(
        Page.id == Revision.page_id,
        Page.current_epoch == Revision.epoch,
    ),
    foreign_keys=[Page.id, Page.current_epoch]
)


class WikiSchemaController(db.ISchemaController):
    models = [Page, Revision, Text]
