# -*- coding: utf-8 -*-
"""
    inyoka.news.models
    ~~~~~~~~~~~~~~~~~~

    Database models for the Inyoka News application.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import datetime, timedelta
from werkzeug import cached_property
from inyoka.core.api import _, ctx, db, cache
from inyoka.core.auth.models import User
from inyoka.core.markup.parser import RenderContext, parse, render
from inyoka.core.models import Tag, TagCounterExtension
from inyoka.portal.api import ILatestContentProvider, ITaggableContentProvider


article_tag = db.Table('news_article_tag', db.metadata,
    db.Column('article_id', db.Integer, db.ForeignKey('news_article.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey(Tag.id))
)


class ArticlesContentProvider(ILatestContentProvider, ITaggableContentProvider):
    type = 'news_articles'
    cache_key = 'news/latest_articles'
    name = _('Articles')

    def get_latest_content(self):
        return Article.query.published() \
            .lightweight(lazy=(Article.comments, Article.author, Article.tags)) \
            .order_by(Article.updated.desc())

    def get_taggable_content(self, tag):
        return tag.articles.order_by('view_count')



class LatestCommentsContentProvider(ILatestContentProvider):
    type = 'news_comments'
    cache_key = 'news/latest_comments'

    def get_latest_content(self):
        return Comment.query.options(db.eagerload('author')) \
                      .order_by(Comment.pub_date).lightweight(lazy=(
                      'author.profile', 'article.tags'))


class CommentMapperExtension(db.MapperExtension):
    def before_insert(self, mapper, connection, instance):
        self.before_update(mapper, connection, instance)

    def before_update(self, mapper, connection, instance):
        context = RenderContext(ctx.current_request)
        node = parse(instance.text)
        instance.rendered_text = node.render(context, 'html')


class CommentCounterExtension(db.AttributeExtension):

    def append(self, state, value, initiator):
        instance = state.obj()
        instance.comment_count += 1
        return value

    def remove(self, state, value, initiator):
        instance = state.obj()
        instance.comment_count -= 1


class Comment(db.Model):
    __tablename__ = 'news_comment'
    __mapper_args__ = {'extension': CommentMapperExtension()}

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    deleted = db.Column(db.Boolean, nullable=False, default=False)
    #TODO: do we really need the rendered text in the database?
    rendered_text = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey(User.id))
    author = db.relationship(User,backref=db.backref('comments', lazy='dynamic'))
    article_id = db.Column(db.Integer, db.ForeignKey('news_article.id'))

    def get_url_values(self, action='view'):
        if action in ('hide', 'restore', 'edit'):
            return 'news/edit_comment', {
                'id': self.id, 'action': action
            }
        return 'news/detail', {
            'slug': self.article.slug,
            '_anchor': 'comment_%s' % self.id
        }

    def __unicode__(self):
        return _(u'Comment by %s on %s') % (
               self.author.display_name, self.article.title
        )


class ArticleQuery(db.Query):

    def published(self):
        """Return a query for all published articles.

        An article is either published if :attr:`Article.public` is `True`
        and :attr:`Article.pub_date` is less or the same than current UTC.
        """
        q = self.filter(db.and_(
            Article.public == True,
            Article.pub_date <= datetime.utcnow(),
        ))
        return q

    def hidden(self):
        """Return a query for not yet published articles.

        To hide an article set :attr:`Article.public` to `False or
        set :attr:`Article.pub_date` to some value in the future.
        """
        q = self.filter(db.or_(
            Article.public == False,
            Article.pub_date > datetime.utcnow()
        ))
        return q

    def by_date(self, year, month=None, day=None):
        """Filter all the items that match the given date."""
        if month is None:
            return self.filter(db.and_(
                Article.pub_date >= datetime(year, 1, 1),
                Article.pub_date < datetime(year + 1, 1, 1)
            ))
        elif day is None:
            return self.filter(db.and_(
                Article.pub_date >= datetime(year, month, 1),
                Article.pub_date < (month == 12 and
                               datetime(year + 1, 1, 1) or
                               datetime(year, month + 1, 1))
            ))
        return self.filter(db.and_(
            Article.pub_date >= datetime(year, month, day),
            Article.pub_date < datetime(year, month, day) +
                             timedelta(days=1)
        ))


class Article(db.Model):
    __tablename__ = 'news_article'
    __mapper_args__ = {
        'extension': db.SlugGenerator('slug', 'title')
    }
    query = db.session.query_property(ArticleQuery)

    id = db.Column(db.Integer, primary_key=True)
    pub_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.utcnow)
    title = db.Column(db.Unicode(200))
    slug = db.Column(db.Unicode(100), unique=True)
    intro = db.Column(db.Text)
    text = db.Column(db.Text)
    public = db.Column(db.Boolean, default=False, nullable=False)
    view_count = db.Column(db.Integer, default=0, nullable=False)
    comment_count = db.Column(db.Integer, default=0, nullable=False)
    comments_enabled = db.Column(db.Boolean, default=True, nullable=False)

    tags = db.relationship(Tag, secondary=article_tag, backref=db.backref(
        'articles', lazy='dynamic'), lazy='joined',
        extension=TagCounterExtension())
    author_id = db.Column(db.ForeignKey(User.id), nullable=False)
    author = db.relationship(User, backref=db.backref('articles', lazy='dynamic'))
    comments = db.relationship(Comment,
        backref=db.backref('article', lazy='joined'),
        primaryjoin=id==Comment.article_id,
        order_by=[db.asc(Comment.pub_date)],
        lazy='dynamic',
        cascade='all, delete, delete-orphan',
        extension=CommentCounterExtension())

    def _render(self, text, key):
        """Render a text that belongs to this Article to HTML.

        We do not use :cls:`~inyoka.core.mixins.TextRendererMixin` because
        we use a more caching aware implementation and need to implement
        two fields to render.
        """
        context = RenderContext(ctx.current_request)
        instructions = cache.get(key)
        if instructions is None:
            instructions = parse(text).compile('html')
            cache.set(key, instructions)
        return render(instructions, context)

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

    @property
    def was_updated(self):
        return self.updated.replace(microsecond=0) > \
               self.pub_date.replace(microsecond=0)

    def touch(self):
        db.atomic_add(self, 'view_count', 1)

    def get_url_values(self, **kwargs):
        action = kwargs.pop('action', 'view')
        if action in ('subscribe', 'unsubscribe'):
            return 'news/subscribe_comments', {
                'slug': self.slug,
                'action': action,
            }

        values = {
            'view': 'news/detail',
            'edit': 'admin/news/article_edit',
            'delete': 'admin/news/article_delete',
        }
        kwargs.update({'slug': self.slug})
        return values[action], kwargs

    def __unicode__(self):
        return self.title
