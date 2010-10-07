# -*- coding: utf-8 -*-
"""
    inyoka.utils.pagination
    ~~~~~~~~~~~~~~~~~~~~~~~

    Helps creating a pagination to split content over several pages.
    Generates the HTML source for the selector and selects the right database
    entries.

    Subclasses of :class:`Pagination` (see below) define different link
    schemes.

    Common usage::

        posts = Posts.query.all()
        pagination = GETPagination(posts, int(request.args.get(page, 1)),
                                   link=u'/posts/', args={'foo':'bar'})
        render_template('posts.html', {'pagination': pagination})

    Template::

        {% for post in pagination.query %}
        {{ post.text }}
        {% endfor %}
        {{ pagination() }}

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import Href, url_encode
from markupsafe import Markup, escape
from inyoka.core.api import ctx
from inyoka.core.exceptions import NotFound
from inyoka.utils.decorators import abstract
from inyoka.i18n import _


class Pagination(object):
    """
    :param query: A SQLAlchemy query object.
    :param page: The page number.
    :param link: The base link for the pagination. If it is not supplied,
                 relative links are used instead.
    :param args: URL parameters, that, if given, are included in the generated
                 urls.
    :param per_page: Number of entries displayed on one page.

    After initialisation, ``pagination.query`` is a list of the matching
    objects.  Call the pagination object for html code of links to the other
    pages.
    """

    # translatable strings for the pagination buttons
    _comma = u'<span class="comma">%s</span>' % escape(_(u', '))
    _next = escape(_(u'next »'))
    _prev = escape(_(u'« previous'))
    _ellipsis = escape(_(u'…'))

    # defaults
    left_threshold = 2
    inner_threshold = 1
    right_threshold = 1
    per_page = 15

    def __init__(self, query, page=None, link=None, args=None, per_page=None):
        self.base_query = query
        self.page = 1 if page is None else page
        if link is not None and not isinstance(link, basestring):
            link = link()
        self.link = link
        self.args = {} if args is None else args
        if per_page is not None:
            self.per_page = per_page

        #TODO: implement position_col
        self.total = self.base_query.count()

        self.pages = (max(0, self.total - 1) // self.per_page) + 1

        if self.page > self.pages or self.page < 1:
            raise NotFound()

        offset = (self.page - 1) * self.per_page
        #TODO: implement position_col
        self.query = query[offset:offset+self.per_page]

    @abstract
    def make_link(self, page):
        """
        Create a link to the given page. Usually used internally only.

        Subclasses must implement this.
        """

    def make_template(self):
        """
        Return a template for creating links. Usually used internally only.

        The template must contain a ``!`` at the place where the page number is
        to be inserted. This is used by JavaScript.

        Subclasses may implement this to enable a JavaScript page selector.
        """
        return None

    def _get_buttons(self, left_threshold=None, inner_threshold=None,
                    right_threshold=None, prev=True, next=True):
        """
        Return the buttons as tuples.
        First item is page number or one of prev, next, ellipsis.
        Second item is link or None if it's the current page or
               (for prev/next) if it's the first or last page
        This is split into a separate method to ease unittesting.
        """
        if left_threshold is None:
            left_threshold = self.left_threshold
        if inner_threshold is None:
            inner_threshold = self.inner_threshold
        if right_threshold is None:
            right_threshold = self.right_threshold

        def include(num, avoidsingle=True):
            if num < 1 or num > self.pages:
                return False

            if num < (left_threshold + 1):
                return True
            if num < self.page and num >= (self.page - inner_threshold):
                return True
            if num == self.page:
                return True
            if num > self.page and num <= (self.page + inner_threshold):
                return True
            if num > (self.pages - right_threshold):
                return True

            if avoidsingle: # avoid 4 ... 6
                if include(num + 1, False) and include(num - 1, False):
                    return True

            return False

        if prev:
            if self.page == 1:
                yield 'prev', None
            else:
                yield 'prev', self.make_link(self.page - 1)

        was_ellipsis = False
        for num in range(1, self.pages + 1):
            if include(num):
                if num == self.page:
                    yield num, None
                else:
                    yield num, self.make_link(num)
                was_ellipsis = False
            else:
                if not was_ellipsis:
                    yield 'ellipsis', self.make_template()
                was_ellipsis = True

        if next:
            if self.page == self.pages:
                yield 'next', None
            else:
                yield 'next', self.make_link(self.page + 1)

    def buttons(self, left_threshold=None, inner_threshold=None,
                right_threshold=None, prev=True, next=True,
                class_=u'pagination', force=False):
        """
        Return HTML code for the page selector if there is more than one page.

        For convenience, the ``__call__`` method is an alias for this.

        :param left_threshold: The number of pages to be shown after the
                               `prev` button.
        :param inner_threshold: The number of pages to be shown before and
                                after the current page.
        :param right_threshold: The number of pages to be shown before the
                                `next` button.
        :param prev: If False, do not show an extra link to the previous page.
        :param next: If False, do not show an extra link to the next page.
        :param class_: The class attribute for the enclosing `div` element.
                       Defaults to `pagination`.
        :param force: If True, return buttons even if there is only one page.
        """

        if self.pages == 1 and not force:
            return Markup(u'')

        ret = []
        add = ret.append
        add(u'<div class="%s">' % class_)

        was_ellipsis = True #no comma at beginning
        for type, link in self._get_buttons(left_threshold=left_threshold,
                                            inner_threshold=inner_threshold,
                                            right_threshold=right_threshold,
                                            prev=prev, next=next):
            if type == 'ellipsis':
                add(u' <span class="ellipsis">%s</span> ' % self._ellipsis)
                if link:
                    add(u'<input type="hidden" class="url-template" value="%s">'
                        % escape(link))
                was_ellipsis = True
                continue

            if not was_ellipsis:
                add(self._comma)
            was_ellipsis = False

            if type == 'prev':
                if link:
                    add(u'<a href="%s" class="prev">%s</a>'
                        % (escape(link), self._prev))
                else:
                    add(u'<span class="prev disabled">%s</span>' % self._prev)
            elif type == 'next':
                if link:
                    add(u'<a href="%s" class="next">%s</a>'
                        % (escape(link), self._next))
                else:
                    add(u'<span class="next disabled">%s</span>' % self._next)
            else:
                _pageclass = ' page1' if type == 1 else '' # required for JS
                if link:
                    add(u'<a href="%s" class="page%s">%d</a>'
                        % (escape(link), _pageclass, type))
                else:
                    add(u'<strong class="page%s">%d</strong>'
                        % (_pageclass, type))

        add(u'</div>')
        return Markup(u''.join(ret))

    def __call__(self, *args, **kwargs):
        """Alias for :meth:`buttons()`."""
        return self.buttons(*args, **kwargs)


class URLPagination(Pagination):
    """
    A Pagination that appends the page number to the URL.
    For example: ``/``, ``/2/``, ``/3/``.
    """
    def make_link(self, page):
        if self.link is None:
            if self.page == 1:
                href = Href()
            else:
                href = Href(u'../')
        else:
            href = Href(self.link)

        if page == 1:
            return href(**self.args)
        return href(u'%d/' % page, **self.args)

    def make_template(self):
        if self.link is None:
            if self.page == 1:
                base = u'!/'
            else:
                base = u'../!/'
        else:
            base = u'%s!/' % self.link

        return Href(base)(**self.args)


class PageURLPagination(Pagination):
    """
    A Pagination that appends `/page/` and the page number to the URL.
    For example: ``/``, ``/page/2/``, ``/page/3/``.
    """
    def make_link(self, page):
        if self.link is None:
            if self.page == 1:
                href = Href()
            else:
                href = Href(u'../../')
        else:
            href = Href(self.link)

        if page == 1:
            return href(**self.args)
        return href(u'page/%d/' % page, **self.args)

    def make_template(self):
        if self.link is None:
            if self.page == 1:
                base = u'page/!/'
            else:
                base = u'../!/'
        else:
            base = u'%spage/!/' % self.link

        return Href(base)(**self.args)


class GETPagination(Pagination):
    """
    A Pagination that passes the page number in the query string.
    For example: ``/``, ``/?page=2``, ``/?page=3``.
    """
    def make_template(self):
        args = self.args.copy()
        args.pop('page', None)
        base = '' if self.link is None else self.link
        if not args:
            return base + '?page=!'
        return u'%s?%s&page=!' % (base, url_encode(args))

    def make_link(self, page):
        args = self.args.copy()
        args['page'] = page
        if page == 1:
            args.pop('page', None)
            if self.link: # avoid query string of only `?`
                return self.link
        return '%s?%s' % (self.link or u'', url_encode(args))


class SearchPagination(GETPagination):
    def __init__(self, page, total, args):
        self.page = page
        self.link = None
        self.args = args
        self.per_page = ctx.cfg['search.count']
        self.total = total

        self.pages = (max(0, self.total - 1) // self.per_page) + 1

        if self.page > self.pages or self.page < 1:
            raise NotFound()

        offset = (self.page - 1) * self.per_page
