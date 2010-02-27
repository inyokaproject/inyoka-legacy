# -*- coding: utf-8 -*-
"""
    inyoka.core.middlewares.debug
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.context import ctx
from inyoka.core.middlewares import IMiddleware
from inyoka.utils.debug import inject_query_info
import re

re_htmlmime = re.compile(r'^text/x?html')


class DebugMiddleware(IMiddleware):

    def __init__(self, ctx):
        IMiddleware.__init__(self, ctx)
        self.enabled = ctx.cfg['debug']

    def process_response(self, request, response):
        if self.enabled and response.status == '200 OK' \
            and re_htmlmime.match(response.content_type):
            inject_query_info(request, response)
        return response
