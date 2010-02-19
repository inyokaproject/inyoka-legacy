# -*- coding: utf-8 -*-
"""
    inyoka.utils.pagination
    ~~~~~~~~~~~~~~~~~~~~~~~

    This file helps creating a pagination.  It's able to generate the HTML
    source for the selector and to select the right database entries.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import math
from werkzeug import Href, url_encode
from inyoka.core.exceptions import NotFound
from inyoka.utils.html import escape
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
    """

    threshold = 3
    left_threshold = 3
    right_threshold = 1
    normal = u'<a href="%(url)s">%(page)d</a>'
    active = u'<strong>%(page)d</strong>'
    commata = u'<span class="commata">,</span>\n'
    ellipsis = u' <span class="ellipsis">…</span>\n'
    template = u'<input type="hidden" class="url-template" value="%s">'

    def __init__(self, query, request=None, page=None, per_page=15, link_func=None):
        if page is None:
            page = 1
        self.request = request
        self.query = query
        self.page = page
        self.per_page = per_page
        self.total = query.count()
        self.pages = int(math.ceil(self.total / float(self.per_page))) or 1
        self.necessary = self.pages > 1

        if link_func is None:
            url_args = {} if self.request is None else self.request.args.copy()
            def link_func(page):
                url_args['page'] = page
                return u'?' + url_encode(url_args)
        self.link_func = link_func

    def __unicode__(self):
        if not self.necessary:
            return u''
        return u'<div class="pagination">%s</div>' % self.generate()

    def make_template(self, page):
        """
        Return a template for creating links. It contains a '!' at the place
        where the page number is to be inserted. This is used by JavaScript.

        Subclasses may implement this to enable a JavaScript page selector.
        """
        return None

    def get_objects(self, raise_not_found=True):
        """Returns the objects for the page."""
        if raise_not_found and self.page < 1:
            raise NotFound()
        rv = self.query.offset(self.offset).limit(self.per_page).all()
        if raise_not_found and self.page > 1 and not rv:
            raise NotFound()
        return rv

    @property
    def offset(self):
        return (self.page - 1) * self.per_page

    def generate(self):
        """This method generates the pagination."""
        was_ellipsis = False
        result = []
        next, prev = None, None

        for num in xrange(1, self.pages + 1):
            if num == self.page:
                was_ellipsis = False
            if num - 1 == self.page:
                next = num
            if num + 1 == self.page:
                prev = num
            if num <= self.left_threshold or \
               num > self.pages - self.right_threshold or \
               abs(self.page - num) < self.threshold:
                if result and result[-1] != self.ellipsis and not was_ellipsis:
                    result.append(self.commata)
                link = self.link_func(num)
                template = num == self.page and self.active or self.normal
                result.append(template % {
                    'url':      link,
                    'page':     num
                })
            elif not was_ellipsis:
                was_ellipsis = True
                result.append(self.ellipsis)
                ellipsis_link = self.make_template(num)
                if ellipsis_link is not None:
                    result.append(self.template % escape(ellipsis_link))

        if next is not None:
            result.append(u'<span class="sep"> </span>'
                          u'<a href="%s" class="next">%s</a>' %
                          (self.link_func(next), _(u'Next »')))
        if prev is not None:
            result.insert(0, u'<a href="%s" class="prev">%s</a> ' %
                          (self.link_func(prev), _(u'« Previous')))

        return u''.join(result)


class URLPagination(Pagination):
    """
    A Pagination that appends the page number to the URL.
    """

    def __init__(self, query, request=None, page=None, per_page=15, link_func=None):
        link_func = link_func or self._link_func
        super(URLPagination, self).__init__(query, request, page, per_page, link_func)

    def _link_func(self, page):
        if page == 1:
            base = '/'
        else:
            base = '../%d/' % page
        args = {} if self.request is None else self.request.args.copy()
        return Href(base)(**args)

    def make_template(self, page):
        if page == 1:
            base = u'!/'
        else:
            base = u'../!/'
        args = {} if self.request is None else self.request.args.copy()
        return Href(base)(args)
