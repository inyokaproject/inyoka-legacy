# -*- coding: utf-8 -*-
"""
    inyoka.utils.sortable
    ~~~~~~~~~~~~~~~~~~~~~

    This module implements a class that makes it easy to handle various
    sortable data.  It automates this process as much as possible.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from jinja2.utils import Markup
from inyoka.i18n import _
from inyoka.core.database import db
from inyoka.core.routing import href
from inyoka.core.context import ctx
from inyoka.utils.html import build_html_tag, escape


class Sortable(object):
    """This class utilizes a sortable table.

    A working example of a box would look like this::

        @templated('portal/users.html')
        def users(request):
            table = Sortable(User.query, 'id', request, ('id', 'username'))
            return {
                'users': table.get_sorted().all(),
                'table': table
            }

    :param query: The query set that should get sorted.  Use the
                  :func:`Sortable.get_objects` function to get it sorted.
    :param default_col: Defines the default sorting mode, required.
    :param request: The current request, optional.
    :param columns: All columns that are usable to sort the model, optional.
    """

    def __init__(self, query, default_col, request=None, columns=None):
        # We need to get the real column objects to give sqlalchemy a chance
        # to resolve the order by column names on complex queries.
        cols = query._mapper_zero().class_.__table__.columns
        columns = dict((x.key, x) for x in cols if columns and x.key in columns or True)
        self.columns = columns
        self.query = query
        self.order_by = (request and request.args.get('order', default_col)
                                 or default_col)
        self.default_col = default_col

    def get_html(self, key, value, nolink=False):
        """
        Returns a HTML link for sorting the table.
        This function is usually called inside the template.

        Usage example in the template file:

        .. sourcecode:: html+jinja

            <tr>
              <th>
                {{ table.get_html('id', '#') }}
              </th>
              <th>
                {{ table.get_html('username', 'Username') }}
              </th>
            </tr>
            {% for user in users %}
              (...)
            {% endfor %}

        :parameter key: The name of the database column that should be used
                        for sorting.
        :param value: The name that is displayed for the link.
        :param nolink: Don't make this column sortable but display a cool link.
        """
        ocol = self.order_by.lstrip('-')
        order = self.order_by.startswith('-')
        if key == ocol:
            new_order = '%s%s' % (('-', '')[order], ocol)
            button = ('down', 'up')[order]
            src = href('static', file='img/%s.png' % button)
            img = build_html_tag('img', src=src)
        else:
            new_order = key
            img = ''

        if nolink:
            return value
        return Markup(u'<a href="?order=%s">%s</a>%s' % (new_order, value, img))

    def get_sorted(self):
        """Return a query object with the proper ordering applied."""
        ocol = escape(self.order_by.lstrip('-'))
        if ocol not in self.columns.keys():
            # safes us from some bad usage that raises an exception
            ctx.current_request.flash(
                _(u'The selected criterium “%s” is not available, '
                  u'falling back to default ordering') % ocol, html=True)
            self.order_by = self.default_col
            ocol = self.order_by.lstrip('-')

        if self.order_by is None:
            return self.query
        order = (db.asc, db.desc)[self.order_by.startswith('-')]
        return self.query.order_by(order(self.columns[ocol]))
