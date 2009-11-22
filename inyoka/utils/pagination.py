# -*- coding: utf-8 -*-
"""
    inyoka.utils.pagination
    ~~~~~~~~~~~~~~~~~~~~~~~

    This file helps creating a pagination.  It's able to generate the HTML
    source for the selector and to select the right database entries.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

from werkzeug import Href
from inyoka.core.exceptions import NotFound
from inyoka.utils import escape
from inyoka.i18n import _

class Pagination(object):
    def __init__(self, query, page, link=None, args=None, per_page=15):
        self.base_query = query
        self.page = page
        self.link = link
        self.args = args
        if args is None:
            self.args = {}
        self.per_page = per_page

        #TODO: add position_col
        self.total = self.base_query.count()

        self.max_pages = (max(0, self.total - 1) // self.per_page) + 1

        if self.page == 1:
            raise NotFound()
        if self.page is None:
            self.page = 1
        if self.page > self.max_pages or self.page < 1:
            raise NotFound()

        index = (self.page - 1) * self.per_page
        #TODO: add position_col
        self.query = query[index:index + self.per_page]

    def make_link(self, page):
        raise NotImplementedError

    def make_template(self):
        return None

    def _get_buttons(self, threshold=2, prev=True, next=True):
        if prev:
            if self.page == 1:
                yield 'prev', None
            else:
                yield 'prev', self.make_link(self.page - 1)

        was_ellipsis = False
        for num in range(1, self.max_pages + 1):
            #: last two ones are to avoid things as `1 ... 3 4`
            if num == self.max_pages or \
               num == 1 or \
               abs(self.page - num) <= 2 or \
               ((self.max_pages - num) <= 1 and (num - self.page) == 3) or \
               (num == 2 and (self.page - num) <= 3):
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
            if self.page == self.max_pages:
                yield 'next', None
            else:
                yield 'next', self.make_link(self.page + 1)

    def buttons(self, threshold=2, prev=True, next=True, class_='pagination'):
        COMMA = '<span class="comma">, </span>'
        NEXT = escape(_(u'next »'))
        PREV = escape(_(u'« previous'))

        ret = []
        add = ret.append
        add(u'<div class="%s">' % class_)

        was_ellipsis = True #no comma at beginning
        for type, link in self._get_buttons(threshold, prev=prev, next=next):
            if type == 'ellipsis':
                add(u'<span class="ellipsis">%s' % escape(_(u' … ')))
                if link:
                    add(u'<input type="hidden" class="url-template" value="%s">'
                        % escape(link))
                add(u'</span>')
                was_ellipsis = True
                continue

            if not was_ellipsis:
                add(COMMA)
            was_ellipsis = False

            if type == 'prev':
                if link:
                    add(u'<a href="%s" class="prev">%s</a>'
                        % (escape(link), PREV))
                else:
                    add(u'<span class="prev disabled">%s</span>' % PREV)
            elif type == 'next':
                if link:
                    add(u'<a href="%s" class="next">%s</a>'
                        % (escape(link), NEXT))
                else:
                    add(u'<span class="next disabled">%s</span>' % NEXT)
            else:
                if link:
                    add(u'<a href="%s" class="page">%d</a>'
                        % (escape(link), type))
                else:
                    add(u'<span class="page current">%d</a>' % type)

        return ''.join(ret)








class URLPagination(Pagination):
    def make_link(self, page):
        """
        Makes a link to the given `page`.
        If the the objects `link` attribute is `None`, a relative link is returned.
        """
        if self.link is None:
            if self.page == 1:
                href = Href()
            else:
                href = Href('../')
        else:
            href = Href(self.link)

        if page == 1:
            return href(self.args)
        return href(u'%d/' % page, self.args)


    def make_template(self):
        if self.link is None:
            if self.page == 1:
                base = u'!/'
            else:
                base = u'../!/'
        else:
            base = u'%s!/' % self.link

        return Href(base)(**self.args)


class GETPagination(Pagination):
    pass