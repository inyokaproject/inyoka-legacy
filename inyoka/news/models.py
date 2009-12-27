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
from werkzeug import cached_property
from inyoka.l10n import to_datetime, rebase_to_timezone
from inyoka.core.api import ctx, _, db, auth, logger, markup, href, cache
from inyoka.utils.text import gen_ascii_slug


class CategoryMapperExtension(db.MapperExtension):
    """This MapperExtension ensures that categories are
    slugified properly.
    """

    def before_insert(self, mapper, connection, instance):
        instance.slug = db.find_next_increment(
            Category.slug, gen_ascii_slug(instance.name)
        )


class ArticleMapperExtension(db.MapperExtension):

    def before_insert(self, mapper, connection, instance):
        if not instance.updated or instance.updated < instance.pub_date:
            instance.updated = instance.pub_date
        instance.slug = db.find_next_increment(
            Article.slug, gen_ascii_slug(instance.subject)
        )

    def after_update(self, mapper, connection, instance):
        """Cleanup caches"""
        cache.delete('news/article_text/%s' % instance.id)
        cache.delete('news/article_intro/%s' % instance.id)


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

    def get_url_values(self, action='view'):
        values = {
            'edit': 'admin/news/category_edit'
        }
        return values[action], {'slug': self.slug}


class Article(db.Model):
    __tablename__ = 'news_article'
    __mapper_args__ = {'extension': ArticleMapperExtension()}

    id = db.Column(db.Integer, primary_key=True)
    pub_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.utcnow)
    subject = db.Column(db.String(200))
    slug = db.Column(db.String(100), unique=True)
    intro = db.Column(db.String)
    text = db.Column(db.String)
    public = db.Column(db.Boolean)

    category_id = db.Column(db.ForeignKey(Category.id), nullable=False)
    category = db.relation(Category)
    author_id = db.Column(db.ForeignKey(auth.User.id), nullable=False)
    author = db.relation(auth.User)

    def _render(self, text, key):
        """Render a text that belongs to this Article to HTML"""
        context = markup.RenderContext(ctx.current_request)
        instructions = cache.get(key)
        if instructions is None:
            instructions = markup.parse(text).compile('html')
            cache.set(key, instructions)
        return markup.render(instructions, context)

    @cached_property
    def rendered_text(self):
        return self._render(self.text, 'news/article_text/%s' % self.id)

    @cached_property
    def rendered_intro(self):
        return self._render(self.intro, 'news/article_intro/%s' % self.id)

    @property
    def hidden(self):
        """
        This returns a boolean whether this article is not visible for normal
        users.
        Article that are not published or whose pub_date is in the future
        aren't shown for a normal user.
        """
        return not self.public or self.pub_date > datetime.utcnow()

    def __unicode__(self):
        return u'%s - %s' % (
            self.pub_date.strftime('%d.%m.%Y'),
            self.subject
        )


class NewsSchemaController(db.ISchemaController):
    models = [Category, Article]
