# -*- coding: utf-8 -*-
"""
    inyoka.news.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the news app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IController, Rule, cache, view
from inyoka.core.http import Response
from inyoka.news.models import Article, Category


def context_modifier(request, context):
    """This function adds two things to the context of all pages:
    `archive`
        A list of the latest months with articles.
    `categories`
        A list of all categories.
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

    categories = Category.query.cached('news/categories')

    context.update(
        MONTHS=dict(enumerate([''] + MONTHS)),
        categories=categories,
        **data
    )

'''
@templated('ikhaya/index.html', modifier=context_modifier)
def index(request, year=None, month=None, category_slug=None, page=1):
    """Shows a few articles by different criteria"""
    category = None
    if year and month:
        articles = Article.objects.filter(
            pub_date__year=year,
            pub_date__month=month
        )
        link = (year, month)
    elif category_slug:
        category = Category.objects.get(slug=category_slug)
        articles = category.article_set.all()
        link = ('category', category_slug)
    else:
        articles = Article.objects.all()
        link = ()

    if not request.user.can('article_read'):
        articles = articles.filter(public=True) \
                           .filter(Q(pub_date__lt=datetime.utcnow().date())|
                                   Q(pub_date = datetime.utcnow().date(), pub_time__lte = datetime.utcnow().time()))

    link = href('ikhaya', *link)
    set_session_info(request, u'sieht sich die <a href="%s">'
                              u'Artikelübersicht</a> an' % link)

    articles = articles.order_by('-updated').select_related()

    pagination = Pagination(request, articles, page, 15, link)

    return {
        'articles':      list(pagination.objects),
        'pagination':    pagination,
        'category':      category
    }


@templated('ikhaya/detail.html', modifier=context_modifier)
def detail(request, year, month, day, slug):
    """Shows a single article."""
    article = Article.objects.select_related().get(
        pub_date=date(int(year), int(month), int(day)),
        slug=slug)
    preview = None
    if article.hidden or article.pub_datetime > datetime.utcnow():
        if not request.user.can('article_read'):
            return AccessDeniedResponse()
        flash(u'Dieser Artikel ist für reguläre Benutzer nicht sichtbar.')
    else:
        set_session_info(request, u'sieht sich den Artikel „<a href="%s">%s'
                         u'</a>“' % (url_for(article), escape(article.subject)))
    if article.comments_enabled and request.method == 'POST':
        form = EditCommentForm(request.POST)
        if 'preview' in request.POST:
            ctx = RenderContext(request)
            preview = parse(request.POST.get('text', '')).render(ctx, 'html')
        elif form.is_valid():
            data = form.cleaned_data
            if data.get('comment_id') and request.user.can('comment_edit'):
                c = Comment.objects.get(id=data['comment_id'])
                c.text = data['text']
                flash(u'Das Kommentar wurde erfolgreich bearbeitet.', True)
            else:
                c = Comment(text=data['text'])
                c.article = article
                c.author = request.user
                c.pub_date = datetime.utcnow()
                flash(u'Dein Kommentar wurde erstellt.', True)
            c.save()
            return HttpResponseRedirect(url_for(article))
    elif request.GET.get('moderate'):
        comment = Comment.objects.get(id=int(request.GET.get('moderate')))
        form = EditCommentForm(initial={
            'comment_id':   comment.id,
            'text':         comment.text,
        })
    else:
        form = EditCommentForm()
    return {
        'article':  article,
        'comments': list(article.comment_set.select_related()),
        'form': form,
        'preview': preview,
        'can_post_comment': request.user.is_authenticated,
        'can_admin_comment': request.user.can('comment_edit'),
        'can_edit_article': request.user.can('article_edit'),
    }

@templated('ikhaya/archive.html', modifier=context_modifier)
def archive(request):
    """Shows the archive index."""
    set_session_info(request, u'sieht sich das <a href="%s">Archiv</a> an' %
                     href('ikhaya', 'archive'))
    months = Article.published.dates('pub_date', 'month')
    return {
        'months': months
    }


'''




class NewsController(IController):
    name = 'news'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/<int:page>/', endpoint='index'),
        Rule('/<date:date>/', endpoint='index'),
        Rule('/<date:date>/<int:page>/', endpoint='index'),
        Rule('/category/<slug>/', endpoint='index'),
        Rule('/category/<slug>/<int:page>/', endpoint='index'),
        Rule('/<date:date>/<slug>/', endpoint='detail'),
        Rule('/archive/', endpoint='archive'),
    ]

    @view('index')
    def index(self, request):
        return Response('this is the news (aka ikhaya) index page')

    @view('entry')
    def entry(self, request, date, slug):
        return Response('this is news entry %r from %s' % (slug, date.strftime('%F')))
