# -*- coding: utf-8 -*-
"""
    inyoka.utils.sortable
    ~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.i18n import _
from inyoka.core.database import db
from inyoka.core.routing import href
from inyoka.core.context import ctx
from inyoka.utils.html import build_html_tag


class Sortable(object):
    """This class utilizes a sortable table.

    A working example of a box would look like this::

        from inyoka.core.auth.models import User
        from inyoka.utils.sortable import Sortable

        @templated('portal/users.html')
        def users(request):
            table = Sortable(User.query, request, 'id', ('id', 'username', 'posts'))
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

    def get_html(self, key, value):
        """
        Returns a HTML link for sorting the table.
        This function is usually called inside the template.

        Usage example in the template file::

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
        """
        ocol = self.order_by.lstrip('-')
        if key == ocol:
            new_order = '%s%s' % (('-', '')[self.order_by.startswith('-')], ocol)
            button = ('down', 'up')[self.order_by.startswith('-')]
            src = href('static', file='img/%s.png' % button)
            img = build_html_tag('img', src=src)
        else:
            new_order = key
            img = ''

        return '<a href="?order=%s">%s</a>%s' % (new_order, value, img)

    def get_sorted(self):
        ocol = self.order_by.lstrip('-')
        if ocol not in self.columns.keys():
            # safes us from some bad usage that raises an exception
            ctx.current_request.flash(
                _(u'The selected criterium “%s” is not available') % ocol
            )
            self.order_by = self.default_col

        if self.order_by is None:
            return self.query
        order = (db.asc, db.desc)[self.order_by.startswith('-')]
        return self.query.order_by(order(self.columns[ocol]))
