# -*- coding: utf-8 -*-
"""
    inyoka.news.models
    ~~~~~~~~~~~~~~~~~~

    Database models for the Inyoka News application-

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import datetime, date
from werkzeug import cached_property
from inyoka.core.api import ctx, db, auth, markup, cache
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
            Article.slug, gen_ascii_slug(instance.title)
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

    def get_url_values(self, action='edit'):
        values = {
            'edit': 'admin/news/category_edit',
            'delete': 'admin/news/category_delete',
        }
        return values[action], {'slug': self.slug}


class ArticleQuery(db.Query):

    def published(self):
        """
        This method returns a query that shows only
        published articles.

        A article is either published if :attr:`Article.public` is `True`
        or :attr:`Article.pub_date` is same and :attr:`Article.pub_time` is
        less then or the same as the current utc date/time.
        """
        q = self.filter(db.and_(
            Article.public == True,
            Article.pub_date < datetime.utcnow(),
        ))
        return q

    def by_date(self, year, month):
        if month == 12:
            next_date = date(year + 1, 1, 1)
        else:
            next_date = date(year, month + 1, 1)

        return self.filter(db.and_(
            Article.pub_date >= date(year, month, 1),
            Article.pub_date < next_date
        ))


class Article(db.Model):
    __tablename__ = 'news_article'
    __mapper_args__ = {'extension': ArticleMapperExtension()}
    query = db.session.query_property(ArticleQuery)

    id = db.Column(db.Integer, primary_key=True)
    pub_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.utcnow)
    title = db.Column(db.String(200))
    slug = db.Column(db.String(100), unique=True)
    intro = db.Column(db.String)
    text = db.Column(db.String)
    public = db.Column(db.Boolean)

    category_id = db.Column(db.ForeignKey(Category.id), nullable=False)
    category = db.relation(Category,
        backref=db.backref('articles', lazy='dynamic'))
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

    def get_url_values(self, action='edit'):
        values = {
            'edit': 'admin/news/article_edit',
            'delete': 'admin/news/article_delete',
        }
        return values[action], {'slug': self.slug}

    def __unicode__(self):
        return u'%s - %s' % (
            self.pub_date.strftime('%d.%m.%Y'),
            self.title
        )


class NewsSchemaController(db.ISchemaController):
    models = [Category, Article]
