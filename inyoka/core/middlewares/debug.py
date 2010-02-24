# -*- coding: utf-8 -*-
"""
    inyoka.core.middlewares.debug
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.context import ctx
from inyoka.core.middlewares import IMiddleware
import logging
from werkzeug import xhtml as html
import re

re_htmlmime = re.compile(r'^text/x?html')


class HtmlLogHandler(logging.Handler):

    def __init__(self):
        logging.Handler.__init__(self)
        self.records = []

    def get_htmllog(self):
        records = []
        for record in self.records:
            records.append(html.div(
              html.h2(html(record.name), ' (', html(record.levelname), '):'),
                html.pre(html(record.getMessage()))
            ))
        records.append('&nbsp')
        return str(html.div(html.div(
            html.h1(u'Inyoka Log'),
            html.p(u'%d records logged' % (len(records)-1)),
            html.script("""
                $(document).ready(function() {
                    function toggleLog() {
                        $('#htmllog').find('h1, h2, pre, p').toggle();
                    }
                    $('<a href="#htmllog">Show/Hide Log</a>').click(toggleLog)
                        .prependTo($('#htmllog-inner'));
                    toggleLog();
                });
                """, type='text/javascript'),
            id_='htmllog-inner'), id_='htmllog'),
            *records)

    def clear(self):
        self.records = []

    def emit(self, record):
        self.records.append(record)

re


class DebugMiddleware(IMiddleware):

    def __init__(self, ctx):
        IMiddleware.__init__(self, ctx)
        self.enabled = ctx.cfg['debug']
        if self.enabled:
            self.handler = HtmlLogHandler()
            engine_log = logging.getLogger('sqlalchemy.engine')
            engine_log.addHandler(self.handler)
            engine_log.setLevel(logging.INFO)

    def process_response(self, request, response):
        if self.enabled and response.status == '200 OK' \
            and re_htmlmime.match(response.content_type):
            response.data = response.data.replace('</body>',
                self.handler.get_htmllog() + '\n</body>', 1)
            self.handler.clear()
        return response
