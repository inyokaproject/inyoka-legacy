# -*- coding: utf-8 -*-
"""
    inyoka.news.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the news app.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import date, datetime
from werkzeug import cached_property
from inyoka.i18n import _
from inyoka.l10n import get_month_names
from inyoka.core.api import IController, Rule, cache, view, templated, href, \
    redirect_to, db, login_required, ctx
from inyoka.core.subscriptions.models import Subscription
from inyoka.news.models import Article, Tag, Comment
from inyoka.news.forms import EditCommentForm
from inyoka.news.subscriptions import ArticleSubscriptionType, \
    CommentSubscriptionType
from inyoka.utils.feeds import atom_feed, AtomFeed
from inyoka.utils.pagination import URLPagination, PageURLPagination


def context_modifier(request, context):
    """This function adds two things to the context of all pages:
    `archive`
        A list of the latest months with articles.
    `tags`
        A list of all tags.
    """
    key = 'news/archive'
    data = cache.get(key)
    if data is None:
        archive = Article.query.dates('pub_date', 'month')
        if len(archive) > 5:
            archive = archive[:5]
            short_archive = True
        else:
            short_archive = False
        data = {
            'archive':       archive,
            'short_archive': short_archive
        }
        cache.set(key, data)

    tags = Tag.query.public().get_cached()
    context.update(
        months=get_month_names(),
        tags=tags,
        active='news',
        **data
    )


class NewsController(IController):
    name = 'news'

    @cached_property
    def url_rules(self):
        url_rules = [
            Rule('/', endpoint='index'),
            Rule('/feed.atom', endpoint='article_feed', defaults={'slug': None}),
            Rule('/+<any(subscribe, unsubscribe):action>',
                 endpoint='subscribe_articles'),
            Rule('/<int:page>/', endpoint='index'),
            Rule('/tag/<slug>/', endpoint='index'),
            Rule('/tag/<slug>/<int:page>/', endpoint='index'),
            Rule('/tag/<slug>/feed.atom', endpoint='article_feed'),
            Rule('/<slug>/', endpoint='detail'),
            Rule('/<slug>/+<any(subscribe, unsubscribe):action>',
                 endpoint='subscribe_comments'),
            Rule('/comment/<int:id>/<any(hide, restore, edit):action>',
                 endpoint='edit_comment'),
            Rule('/archive/', endpoint='archive'),
        ]

        # add the more complex url rule for archive and show post
        tmp = '/archive/'
        for digits, part in zip((4, 2, 2), ('year', 'month', 'day')):
            tmp += '<int(fixed_digits=%d):%s>/' % (digits, part)
            url_rules.extend([
                Rule(tmp, defaults={'page': 1}, endpoint='archive'),
                Rule(tmp + 'page/<int:page>/', endpoint='archive'),
            ])
        return url_rules

    @view('index')
    @templated('news/index.html', modifier=context_modifier)
    def index(self, request, slug=None, page=1):
        tag = None
        if slug:
            tag = Tag.query.public().filter_by(slug=slug).one()
            articles = tag.articles
        else:
            articles = Article.query

        #TODO: add ACL for public articles
        articles = articles.order_by(Article.updated.desc())

        pagination = URLPagination(articles, page, per_page=10)

        return {
            'articles':      pagination.query,
            'pagination':    pagination,
            'tag':           tag
        }

    @view('detail')
    @templated('news/detail.html', modifier=context_modifier)
    def detail(self, request, slug):
        article = Article.query.filter_by(slug=slug).one()
        if article.hidden:
            #TODO: ACL Check
            request.flash(_(u'This article is hidden'), False)

        if article.comments_enabled:
            form = EditCommentForm(request.form)
            if form.validate_on_submit():
                if form.data.get('comment_id', None):
                    comment = Comment.query.get(form.comment_id.data)
                    comment.text = form.text.data
                    request.flash(_(u'The comment was successfully edited'), True)
                else:
                    comment = Comment(text=form.text.data, author=request.user)
                    article.comments.append(comment)
                    Subscription.new(comment, 'news.comment.new')
                    request.flash(_(u'Your comment was successfully created'), True)
                db.session.commit()
                return redirect_to(comment)
        else:
            form = EditCommentForm()

        # increase counters
        article.touch()

        comments = list(article.comments.options(db.joinedload('author')))
        Subscription.accessed(request.user, object=article, subject=article)

        return {
            'article':  article,
            'comments': comments,
            'form': form
        }

    @login_required
    @view('edit_comment')
    @templated('news/edit_comment.html', modifier=context_modifier)
    def change_comment(self, request, id, action):
        comment = Comment.query.get(id)
        if action in ('hide', 'restore'):
            comment.deleted = False if action == 'restore' else True
            db.session.commit()
            request.flash(_(u'The comment was hidden') if action == 'hide' \
                else _(u'The comment was restored'))
            return redirect_to(comment)

        # action == 'edit'
        form = EditCommentForm(request.form)
        if form.validate_on_submit():
            if form.validate():
                comment.text = form.text.data
                db.session.commit()
                request.flash(_(u'The comment was saved'), True)
                return redirect_to(comment)
        else:
            form.text.data = comment.text
        return {
            'comment':  comment,
            'form':     form,
        }

    @view('archive')
    @templated('news/archive.html', modifier=context_modifier)
    def archive(self, request, year=None, month=None, day=None, page=1):
        if not year:
            ret = {
                'month_list': True,
                'articles': Article.query.dates('pub_date', 'month', dt_obj=True)
            }
            return ret

        query = Article.query.published().by_date(year, month, day)

        pagination = PageURLPagination(query, page=page, per_page=5)

        ret = dict(year=year, month=month, day=day,
            date=date(year, month or 1, day or 1),
            month_list=False,
            pagination=pagination,
            articles=pagination.query)
        return ret

    @login_required
    @view('subscribe_articles')
    def subscribe_articles(self, request, action):
        do = {
            'subscribe': Subscription.subscribe,
            'unsubscribe': Subscription.unsubscribe,
        }[action]
        existed = do(request.user, ArticleSubscriptionType)

        msg = {
            'subscribe': [_(u'You had already been subscribed before.'),
                          _(u'You have successfully been subscribed to '
                            u'new News articles.')],
            'unsubscribe':[_(u'You had not been subscribed before.'),
                           _(u'You have successfully been unsubscribed from '
                             u'new News articles.')],
        }
        request.flash(msg[action][existed], True if not existed else None)

        return redirect_to('news/index')

    @login_required
    @view('subscribe_comments')
    def subscribe_comments(self, request, action, slug):
        do = {
            'subscribe': Subscription.subscribe,
            'unsubscribe': Subscription.unsubscribe,
        }[action]
        article = Article.query.filter_by(slug=slug).one()
        existed = do(request.user, CommentSubscriptionType, article)

        msg = {
            'subscribe': [_(u'You had already been subscribed before.'),
                          _(u'You have successfully been subscribed to '
                            u'new comments on this article.')],
            'unsubscribe':[_(u'You had not been subscribed before.'),
                           _(u'You have successfully been unsubscribed from '
                             u'new comments on this article.')],
        }
        request.flash(msg[action][existed], True if not existed else None)
        return redirect_to(article)

    @atom_feed('news/feeds/articles/%(slug)s', 'article_feed')
    def article_feed(self, request, slug=None):
        """
        Shows all news entries that match the given criteria in an atom feed.
        """
        query = Article.query
        title = u'News'

        if slug:
            # filter the articles matching a defined tag
            tag = Tag.query.public().filter_by(slug=slug).one()
            query = tag.articles
            title = _(u'News for %s' % slug)

        query = query.options(db.eagerload('author')) \
                     .order_by(Article.updated.desc()).limit(20)

        feed = AtomFeed(_(u'%s – %s' % (title, ctx.cfg['website_title'])),
            feed_url=request.url, url=request.url_root,
            icon=href('static', file='img/favicon.ico'))

        for article in query.all():
            feed.add(article.title,
                u'%s\n%s' % (article.rendered_intro, article.rendered_text),
                content_type='html', url=href(article, _external=True),
                author={
                    'name': article.author.display_name,
                    'uri': href(article.author.profile)
                },
                id=article.id, updated=article.updated, published=article.pub_date)

        return feed
