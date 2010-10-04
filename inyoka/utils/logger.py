# -*- coding: utf-8 -*-
"""
    inyoka.utils.logger
    ~~~~~~~~~~~~~~~~~~~

    This module provides a logger.

    :copyright: 2007-2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from logbook import Logger
from logbook.more import ColorizedStderrHandler as ColorizedStderrHandlerBase


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
