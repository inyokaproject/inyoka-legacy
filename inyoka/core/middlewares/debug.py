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


class DebugHandler(logging.Handler):

    def __init__(self):
        logging.Handler.__init__(self)
        self.records = []

    def get_htmllog(self):
        records = []
        for record in self.records:
            records.append(html.div(
              html.h2(html(record.name), ' (', html(record.levelname), '):'),
                html.p(html(record.getMessage()), class_='message')
            ))
        return str(html.div(
            html.h1(u'Debug Log'),
            html.p(u'%d records logged' % len(records)),
            html.script("""
                $(document).ready(function() {
                    function toggleLog() {
                        $('#html_log h1, #html_log h2, #html_log p').toggle();
                    }
                    $('<a href="#html_log">Show/Hide Debug Log</a>').click(toggleLog)
                        .prependTo($('#html_log'));
                    toggleLog();
                });
                """, type='text/javascript'),
            html.br(style='clear: both;'),
            *records,
            id_='html_log'))

    def clear(self):
        self.records = []

    def emit(self, record):
        self.records.append(record)



class DebugMiddleware(IMiddleware):

    def __init__(self, ctx):
        IMiddleware.__init__(self, ctx)
        self.handler = DebugHandler()
        engine_log = logging.getLogger('sqlalchemy.engine')
        engine_log.addHandler(self.handler)
        engine_log.setLevel(logging.INFO)

    def process_response(self, request, response):
        response.data = response.data.replace('</body>',
            self.handler.get_htmllog() + '\n</body>', 1)
        self.handler.clear()
        return response
