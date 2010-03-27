# -*- coding: utf-8 -*-
"""
    inyoka.core.models
    ~~~~~~~~~~~~~~~~~~

    Core models not specific to a single app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
import random
import string

from datetime import date, datetime, timedelta
from sqlalchemy.orm import MapperExtension
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from inyoka.core.database import db
from inyoka.core.context import ctx
from inyoka.core.routing import href
from inyoka.core.serializer import SerializableObject
from inyoka.utils.diff3 import prepare_udiff, generate_udiff


CONFIRM_ACTIONS = {}


tag_re = re.compile(r'[\w-]{2,20}')


class TagQuery(db.Query):

    def get_cached(self):
        """This method is a wrapper around common tag caching
        to not write the cache key everywhere in the code"""
        return self.cached('core/tags')


class Tag(db.Model, SerializableObject):
    __tablename__ = 'core_tag'
    __mapper_args__ = {'extension': db.SlugGenerator('slug', 'name')}

    query = db.session.query_property(TagQuery)

    #: serializer attributes
    object_type = 'core.tag'
    public_fields = ('id', 'name', 'slug')

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, index=True)
    slug = db.Column(db.String(20), nullable=False, unique=True)

    def __unicode__(self):
        return self.name

    @db.validates('name')
    def validate_tag(self, key, tag):
        if not tag_re.match(tag):
            raise ValueError(u'Invalid tag name %s' % tag)
        return tag

    def get_url_values(self, action='view'):
        values = {
            'view': 'portal/tags',
            'edit': 'admin/portal/tag_edit',
            'delete': 'admin/portal/tag_delete',
        }
        return values[action], {'slug': self.slug}


class ConfirmMapperExtension(MapperExtension):

    def before_insert(self, mapper, connection, instance):
        while instance.key is None:
            key = mapper.class_._make_key()
            if Confirm.query.get(key) is None:
                instance.key = key


class ConfirmQuery(db.Query):

    def get(self, pk):
        if isinstance(pk, basestring):
            try:
                return self.filter_by(key=pk).one()
            except (NoResultFound, MultipleResultsFound):
                return None
        return super(ConfirmQuery, self).get(pk)


class Confirm(db.Model):
    """
    Holds the data for a confirm action.

    :param action: The key of the wanted action.
    :param expires: Defines when the confirm should expire. This is only
                    accurate to one day. This may either be a datetime or date,
                    a timedelta or an integer, which is then considered the
                    time until expiration in days. If the link is called after
                    it is expired, the user is rejected.
    :param data: Data which is passed to the registered function when the link
                 is accessed. It is saved pickled, so make sure your object is
                 pickleable.
    """

    __tablename__ = 'core_confirm'
    __mapper_args__ = {
        'extension': ConfirmMapperExtension(),
    }
    query = db.session.query_property(ConfirmQuery)

    _key_length = 32
    _key_chars = string.ascii_letters + string.digits

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), unique=True)
    action = db.Column(db.String(40))
    data = db.Column(db.PickleType)
    expires = db.Column(db.Date)

    def __init__(self, action, data, expires):
        if action not in CONFIRM_ACTIONS:
            raise KeyError('Action %r is not registered.' % action)

        if isinstance(expires, (datetime, date)):
            self.expires = expires
        elif isinstance(expires, timedelta):
            self.expires = date.today() + expires
        else:
            self.expires = date.today() + timedelta(days=expires)

        self.action = action
        self.data = data
        db.session.add(self)

    def __repr__(self):
        return '<Confirm %s %s>' % (self.action, getattr(self, 'key', ''))

    @classmethod
    def _make_key(cls):
        return ''.join(random.choice(cls._key_chars) for _
                       in range(cls._key_length))

    @property
    def url(self):
        return href('portal/confirm', key=self.key, _external=True)

    @property
    def is_expired(self):
        return self.expires < date.today()


class RevisionedModelMixin(object):
    """A mixin to implement some common functions used on revisioned models.

    Some usage example::

        class PasteEntry(db.Model):
            __tablename__ = 'pastes'
            id = db.Column(db.Integer, primary_key=True)
            code = db.Column(db.Text)

    This is some standalone model.  Now that we want to make it implement
    revisions.  For that this mixin relies on one additional column.
    A ``parent_id`` that points to the paste entry model.

    Now we've done that our model looks like that::

        class PasteEntry(db.Model, RevisionedModelMixin):
            __tablename__ = 'pastes'
            id = db.Column(db.Integer, primary_key=True)
            code = db.Column(db.Text)
            parent_id = db.Column(db.Integer, db.ForeignKey('pastes.id'))

    With that you can use the tree additional functions
    :func:`~RevisionedModelMixin.resolve_root`,
    :func:`~RevisionedModelMixin.fetch_replies,
    :func:`~RevisionedModelMixin.compare_to`, see those documentation for
    more detail.
    """

    @classmethod
    def resolve_root(cls, identifier):
        """Find the root for a tree.

        :param identifier: The identifier a model should queried for.
                           We use ``cls.query.get`` to query the identifier.
        :returns: The very root object with no additional parent_id set.
        """
        obj = cls.query.get(identifier)
        if obj is None:
            return
        while obj.parent_id is not None:
            obj = obj.parent
        return obj

    def fetch_replies(self):
        """Get new replies for the model.

        Those replies only match the current active instance.
        """
        cls = self.__class__
        obj_list = cls.query.filter(db.and_(
            cls.parent_id.in_([self.id]),
        )).order_by(cls.id.desc()).all()

        return obj_list

    def compare_to(self, other, column, context_lines=4, template=False):
        """Compare the mdoel with another revision.

        :param other: The other model instance to compare with.
        :param column: A string what column to compare.
        :param context_lines: How many additional lines to show on the udiff.
        :param template: Either or not to prepare the udiff for templates use.
        """
        udiff = generate_udiff(
            old=getattr(self, column, u''),
            new=getattr(other, column, u''),
            old_title=unicode(self),
            new_title=unicode(other),
            context_lines=context_lines
        )

        if template:
            diff, info = prepare_udiff(udiff)
            return diff and diff[0] or None
        return udiff


class CoreSchemaController(db.ISchemaController):
    models = [Confirm, Tag]
