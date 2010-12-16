# -*- coding: utf-8 -*-
"""
    inyoka.wiki.models
    ~~~~~~~~~~~~~~~~~~

    Models for the wiki.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import datetime
from sqlalchemy.ext.associationproxy import association_proxy
from inyoka.core.api import db, href, _
from inyoka.core.mixins import TextRendererMixin
from inyoka.core.search import SearchIndexMapperExtension
from inyoka.core.auth.models import User
from inyoka.wiki.utils import urlify_page_name
from inyoka.utils.highlight import highlight_text



class PageQuery(db.Query):
    def filter_name(self, name):
        return self.filter(db.func.lower(Page.name)==name.lower())

    def get(self, pk):
        """
        Return the page with the given name or id (None if it does not exist).

        You usually should not use this function in views directly to ensure
        proper redirection (/maIN_paGE -> /Main_Page). Use
        :meth:`wiki.utils.find_page` instead.
        """
        if isinstance(pk, basestring):
            try:
                return Page.query.filter_name(pk).one()
            except db.NoResultFound:
                return
        return super(PageQuery, self).get(pk)

    def exists(self, name):
        return bool(self.filter_name(name).count())


class PageDeleted(ValueError):
    pass

class PageExists(ValueError):
    pass


class Page(db.Model):
    __tablename__ = 'wiki_page'
    __mapper_args__ = {
        'extension': SearchIndexMapperExtension('portal', 'wiki'),
    }

    query = db.session.query_property(PageQuery)


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(200), index=True, nullable=False)
    current_revision_id = db.Column(db.Integer,
        db.ForeignKey('wiki_revision.id', name='current_revision_id',
                      use_alter=True)) # avoid circular dependency
    current_epoch = db.Column(db.Integer, default=1, nullable=False)
    deleted = db.Column(db.Boolean, nullable=False, default=False)

    current_revision = db.relationship('Revision', post_update=True,
        primaryjoin='Page.current_revision_id == Revision.id')

    def __repr__(self):
        return '<Page %r>' % self.name

    @staticmethod
    def create_or_edit(name, **kwargs):
        """
        Like Page.create but does edit the page if it already exists.
        """
        try:
            return Page.create(name, **kwargs)
        except PageExists:
            p = Page.query.get(name)
            p.edit(**kwargs)
            return p

    @staticmethod
    def create(name, **kwargs):
        """
        Create a new page and return it.

        :param page: The name for the new page.
        All other params are the same as for Page.edit().

        If the page does not exist, create it and add a first revision with
        the given data.
        If the page does exist but is deleted, increment the epoch and create
        a new revision with the given data.
        Else raise `PageExists` exception.
        """
        _was_deleted = False

        p = Page.query.get(name)
        if p is None:
            p = Page(name=name)
            p.current_epoch = 1
        elif p.deleted:
            p.deleted = False
            _was_deleted = True
        else:
            raise PageExists(u'A page with that name already exists.')

        p.edit(_was_deleted=_was_deleted, **kwargs)
        return p

    def edit(self, change_user, change_comment=None, text=None,
             change_date=None, _was_deleted=False, attachment=None):
        """
        Create a new revision for this page.

        :param change_user: The user making the change.
        :param change_comment: The user's comment on the change.
        :param change_date: Date of the change. Defaults to utcnow.
        :param text: New text of the page. Defaults to current text.
        :param attachment: A FileStorage object pointing to a file that shall
                           be attached to the page.
        """
        if self.deleted:
            raise PageDeleted(u'This page is deleted and cannot be edited. '
                              u'Use Page.create() instead.')

        r = Revision(page=self, epoch=self.current_epoch)

        r.change_user = change_user
        r.change_comment = change_comment
        r.change_date = change_date

        if text is None:
            if self.current_revision is None or _was_deleted:
                raise ValueError('text may not be None for new page')
            r.text_id = self.current_revision.text_id
        else:
            r.raw_text = text

        if attachment:
            att = Attachment(file=attachment)

        self.current_revision = r
        db.session.commit()

        if attachment:
            r.attachment_id = att.id
            db.session.commit()

    def delete(self):
        self.deleted = True
        self.current_epoch += 1
        db.session.commit()

    def get_attachment_pages(self):
        """
        Return a list of the pages that contain files attached to this page.
        """
        return Page.query.join(Page.current_revision).filter(
            Page.name.startswith(self.name + u'/') &
            (Revision.attachment_id > 0)
        ).options(db.joinedload_all(Page.current_revision, Revision.attachment))

    @property
    def is_attachment_page(self):
        return self.current_revision.attachment_id is not None

    @property
    def url_name(self):
        return urlify_page_name(self.name)

    def get_url_values(self, action='show', revision=None, old_rev=None,
                       new_rev=None):
        if action == 'show':
            return 'wiki/show', {
                'page': self.url_name,
                'revision': getattr(revision, 'id', revision)
            }
        elif action in ('history', 'edit', 'attachments'):
            return 'wiki/%s' % action, {'page': self.url_name}
        elif action in ('diff', 'udiff'):
            return 'wiki/diff', {'page': self.url_name, 'old_rev': old_rev,
                                 'new_rev': new_rev, 'format': action}


class Text(db.Model, TextRendererMixin):
    __tablename__ = 'wiki_text'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column('text', db.Text, nullable=False)

    def __repr__(self):
        return '<Text #%r>' % self.id


class Attachment(db.Model):
    """
    Revisions can have uploaded data associated, this table holds the
    mapping to the uploaded file on the file system.
    """
    __tablename__ = 'wiki_attachment'

    id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.File(save_to='wiki/attachments'))

    @property
    def html_representation(self):
        """
        This method returns a `HTML` representation of the attachment for the
        `show_action` page.  If this method does not know about an internal
        representation for the object the return value will be an download
        link to the raw attachment.
        """
        url = href(self)
        t = u'<a href="%s">%s</a>' % (url, _(u'Download attachment'))
        if self.file.mimetype.startswith('image/'):
            # TODO: This should be thumbnailed
            return u'<a href="%s"><img class="attachment" src="%s" ' \
                   u'alt="%s"></a>' % ((url,) * 3)
        elif self.file.mimetype.startswith('text/'):
            # TODO: This loads the whole file into memory
            return highlight_text(self.file.contents,
                                  filename=self.file.filename) + t
        else:
            return t

    def get_url_values(self, action='show'):
        return 'media', {'file': self.file.filename}


def _create_text(value):
    return Text(text=value)


class Revision(db.Model):
    __tablename__ = 'wiki_revision'

    id = db.Column(db.Integer, primary_key=True)
#    revision = db.Column(db.Integer, nullable=False)
    page_id = db.Column(db.ForeignKey(Page.id), nullable=False)
    change_user_id = db.Column(db.ForeignKey(User.id), nullable=False)
    change_date = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    change_comment = db.Column(db.Unicode(512))
    text_id = db.Column(db.ForeignKey(Text.id))
    epoch = db.Column(db.Integer, nullable=False)
    attachment_id = db.Column(db.ForeignKey(Attachment.id))

    page = db.relationship(Page, primaryjoin='Revision.page_id == Page.id',
        backref=db.backref('all_revisions', lazy='dynamic',
                           cascade='all, delete, delete-orphan'))
    text = db.relationship(Text)
    change_user = db.relationship(User)
    attachment = db.relationship(Attachment)

    raw_text = association_proxy('text', 'text', creator=_create_text)
    rendered_text = association_proxy('text', 'rendered_text')

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
