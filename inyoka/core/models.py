# -*- coding: utf-8 -*-
"""
    inyoka.core.models
    ~~~~~~~~~~~~~~~~~~

    Core models not specific to a single app.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
import random
import string
import math
from datetime import date, datetime, timedelta
from sqlalchemy.orm import MapperExtension
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm.dynamic import AppenderQuery
from sqlalchemy.orm.properties import RelationshipProperty
from inyoka import Interface
from inyoka.core.database import db
from inyoka.core.context import ctx
from inyoka.core.routing import href
from inyoka.core.serializer import SerializableObject
from inyoka.utils.diff3 import prepare_udiff, generate_udiff
from inyoka.utils.decorators import abstract


CONFIRM_ACTIONS = {}


tag_re = re.compile(r'[\w-]{2,20}')


def _calculate_thresholds(min_weight, max_weight, steps):
    delta = (max_weight - min_weight) / float(steps)
    return [min_weight + i * delta for i in range(1, steps + 1)]


def _calculate_tag_weight(weight, max_weight):
    """Lograithmic tag weight calculation"""
    return math.log(weight) * max_weight / math.log(max_weight)


class TagCounterExtension(db.AttributeExtension):
    """Counts the comments on the post."""

    def append(self, state, value, initiator):
        db.atomic_add(value, 'tagged', 1)
        return value

    def remove(self, state, value, initiator):
        db.atomic_add(value, 'tagged', -1)
        return value


class TagQuery(db.Query):

    def get_cached(self):
        """This method is a wrapper around common tag caching
        to not write the cache key everywhere in the code"""
        return self.order_by(Tag.tagged.asc()).cached('core/tags')

    def public(self):
        """This method returns a query that shows only public tags."""
        return self.filter(Tag.public == True)

    def get_cloud(self, max_visible=None, steps=4):
        """Get all informations required for a tag cloud

        Returns a tuple containing the items and a boolean indicating
        whether there are more tags to show or not.
        """
        if max_visible is None:
            tags = self.get_cached()
            tag_count = len(tags)
        else:
            tags = self.order_by(Tag.tagged.desc()).limit(max_visible).all()
            tag_count = self.count()

        if not tag_count:
            return [], False

        items = []
        counts = [tag.tagged for tag in tags]
        min_weight = float(min(counts))
        max_weight = float(max(counts))
        thresholds = _calculate_thresholds(min_weight, max_weight, steps)
        for tag in tags:
            item = {
                'id': tag.id,
                'name': tag.name,
                'slug': tag.slug,
                'count': tag.tagged,
                'size': 80
            }
            if item['count']:
                font_set = False
                for idx in xrange(steps):
                    tag_weight = _calculate_tag_weight(item['count'] or 1, max_weight)
                    if not font_set and tag_weight <= thresholds[idx]:
                        item['size'] += tag_weight * idx
                        font_set = True
                item['size'] = int(item['size'])
            items.append(item)

        items.sort(key=lambda x: x['name'].lower())
        more = False if max_visible is None else tag_count > max_visible
        return items, more


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
    #: Number of items tagged
    tagged = db.Column(db.Integer, nullable=False, default=0)
    #: Flag if the tag is public or internal.  If a tag is not public
    #: it's probably used by internal functions to ensure special
    #: permission flags.  It's not shown in any public interface (e.g tag-cloud)
    public = db.Column(db.Integer, nullable=False, default=True)

    def __unicode__(self):
        return self.name

    @db.validates('name')
    def validate_tag(self, key, tag):
        if not tag_re.match(tag):
            raise ValueError(u'Invalid tag name %s' % tag)
        return tag

    def get_url_values(self, action='view'):
        values = {
            'view': 'portal/tag',
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


class CoreSchemaController(db.ISchemaController):
    models = [Confirm, Tag]
