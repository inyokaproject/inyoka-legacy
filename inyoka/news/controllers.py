# -*- coding: utf-8 -*-
"""
    inyoka.news.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the news app.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import date, datetime
from inyoka.i18n import _
from inyoka.l10n import get_month_names
from inyoka.core.api import IController, Rule, cache, view, templated, href, \
    redirect_to, db
from inyoka.core.http import Response
from inyoka.core.exceptions import Forbidden
from inyoka.news.models import Article, Tag, Comment
from inyoka.news.forms import EditCommentForm
from inyoka.utils.pagination import URLPagination


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

    tags = Tag.query.get_cached()
    context.update(
        months=get_month_names(),
        tags=tags,
        active='news',
        **data
    )


class NewsController(IController):
    name = 'news'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/<int:page>/', endpoint='index'),
        Rule('/tag/<slug>/', endpoint='index'),
        Rule('/tag/<slug>/<int:page>/', endpoint='index'),
        Rule('/<slug>/', endpoint='detail'),
        Rule('/archive/', endpoint='archive'),
        Rule('/archive/<int(fixed_digits=4):year>/', endpoint='archive'),
        Rule('/archive/<int(fixed_digits=4):year>/<int(fixed_digits=2):month>/',
             endpoint='archive'),
        Rule('/archive/<int(fixed_digits=4):year>/<int(fixed_digits=2):month>/'
             '<int(fixed_digits=2):day>/', endpoint='archive'),
        Rule('/comment/<int:id>/<any(hide, restore, edit):action>',
             endpoint='edit_comment')
    ]

    @view('index')
    @templated('news/index.html', modifier=context_modifier)
    def index(self, request, slug=None, page=1):
        tag = None
        if slug:
            tag = Tag.query.filter_by(slug=slug).one()
            articles = tag.articles
        else:
            articles = Article.query

        #TODO: add ACL for public articles
        articles = articles.order_by('-updated')

        pagination = URLPagination(articles, page=page, per_page=10)

        return {
            'articles':      pagination.get_objects(),
            'pagination':    pagination,
            'tag':           tag
        }

    @view('detail')
    @templated('news/detail.html', modifier=context_modifier)
    def detail(self, request, slug):
        article = Article.query.filter_by(slug=slug).one()
        if article.hidden or article.pub_date > datetime.utcnow():
            #TODO: ACL-Check
            return Forbidden()

        if article.comments_enabled and request.method == 'POST':
            form = EditCommentForm()
            if form.validate(request.form):
                if form.data.get('comment_id'):
                    comment = Comment.query.get(data['comment_id'])
                    comment.text = form.data['text']
                    request.flash(_(u'The comment was successfully edited'), True)
                else:
                    comment = Comment(text=form.data['text'], article=article,
                                      author=request.user)
                    request.flash(_(u'Your comment was successfully created'), True)
                db.session.commit()
                return redirect_to(comment)
        else:
            form = EditCommentForm()

        # if everything is valid, update the visit counter
        db.atomic_add(article, 'visit_count', 1, expire=True)
        db.session.commit()

        return {
            'article':  article,
            'comments': list(article.comments.options(db.eagerload('author'))),
            'form': form.as_widget(),
        }

    @view('edit_comment')
    @templated('news/edit_comment.html', modifier=context_modifier)
    def change_comment(self, request, id, action):
        comment = Comment.query.get(id)
        if action in ('hide', 'restore'):
            comment.deleted = ('restore', 'hide').index(action)
            db.session.commit()
            request.flash(_(u'The comment was hidden') if action == 'hide' \
                else _(u'The comment was restored'))
            return redirect_to(comment)

        # action == 'edit'
        if request.method == 'POST':
            form = EditCommentForm()
            if form.validate(request.form):
                comment.text = form.data['text']
                db.session.commit()
                request.flash(_(u'The comment was saved'), True)
                return redirect_to(comment)
        else:
            form = EditCommentForm(initial={'text': comment.text})
        return {
            'comment':  comment,
            'form':     form.as_widget(),
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

        url_args = dict(year=year, month=month, day=day)
        query = Article.query.published().by_date(year, month, day)
        pagination = URLPagination(query, page=page, per_page=15)

        ret = dict(year=year, month=month, day=day,
            date=date(year, month or 1, day or 1), month_list=False,
            pagination=pagination, articles=pagination.get_objects())
        return ret
