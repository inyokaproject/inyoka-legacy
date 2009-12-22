# -*- coding: utf-8 -*-
"""
    inyoka.news.models
    ~~~~~~~~~~~~~~~~~~

    Database models for the Inyoka News application-

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from hashlib import md5
from datetime import datetime, date
from inyoka.l10n import to_datetime, rebase_to_timezone
from inyoka.core.api import ctx, _, db, auth, logger, markup, href, cache, \
    current_request
from inyoka.utils.text import gen_ascii_slug


class CategoryMapperExtension(db.MapperExtension):
    """This :cls:`MapperExtension` ensures that categories are
    slugified properly.
    """

    def before_insert(self, mapper, connection, instance):
        instance.slug = db.find_next_increment(
            Category.slug, gen_ascii_slug(instance.name)
        )


class Category(db.Model):
    __tablename__ = 'news_category'
    __mapper_args__ = {'extension': CategoryMapperExtension()}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        if self.id is None:
            return '<Category [orphan] (%s)>' % self.slug
        return '<Category #%d (%s)>' % (
            self.id,
            self.slug,
        )
    def __unicode__(self):
        return self.name

    def get_absolute_url(self, action='show'):
        return href(*{
        }[action])


class NewsSchemaController(db.ISchemaController):
    models = [Category]
