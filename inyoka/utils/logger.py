# -*- coding: utf-8 -*-
"""
    inyoka.utils.logger
    ~~~~~~~~~~~~~~~~~~~

    This module provides a logger.

    :copyright: 2007-2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from logbook import Logger, Processor
from logbook.base import ERROR, WARNING, INFO, DEBUG
from logbook.more import ColorizedStderrHandler as ColorizedStderrHandlerBase

from inyoka.context import ctx


def make_request_info_injector(request):
    def inject_request_info(record):
        record.extra.update(
            ip=request.remote_addr,
            method=request.method,
            url=request.url)
    return inject_request_info


class RequestProcessor(Processor):
    def __init__(self, request):
        Processor.__init__(self, make_request_info_injector(request))


class ColorizedStderrHandler(ColorizedStderrHandlerBase):
    def get_color(self, record):
        if record.level >= ERROR:
            return 'red'
        elif record.level >= WARNING:
            return 'yellow'
        elif record.level == INFO:
            return 'green'
        elif record.level == DEBUG:
            return 'blue'
        return 'white'


logger = Logger('inyoka')
logbook_handler = ColorizedStderrHandler()
logbook_handler.push_application()
