# -*- coding: utf-8 -*-
"""
    inyoka.utils.logger
    ~~~~~~~~~~~~~~~~~~~

    This module provides a logger.

    :copyright: 2007-2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from os import environ
import sys
import logging
from logging import Formatter
from inyoka import INYOKA_REVISION
from inyoka.core.context import config
from inyoka.utils.colors import blue, green, red, yellow, white



def _level_aware_colorizer(level):
    levels = {
        'CRITICAL': red,
        'ERROR':    red,
        'WARN':     yellow,
        'WARNING':  yellow,
        'INFO':     green,
        'DEBUG':    blue,
        'NOTSET':   white
    }
    colorized = '[%(levelname)s %(asctime)s]'
    message = ' %(message)s'

    return levels[level](colorized) + message


class SimpleFormatter(Formatter):

    _date_fmt = '%Y-%m-%d %H:%M:%S'

    def __init__(self, fmt=None, datefmt=None, use_color=True):
        Formatter.__init__(self, fmt, self._date_fmt)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        log_format = _level_aware_colorizer(levelname)
        record.message = record.getMessage()
        record.asctime = self.formatTime(record, self.datefmt)
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        dct = dict(record.__dict__)
        dct['revision'] = INYOKA_REVISION
        return log_format % dct


logger = logging.getLogger('inyoka')
logging_handler = logging.StreamHandler(sys.stdout)
logging_handler.setFormatter(SimpleFormatter())
logger.addHandler(logging_handler)

if config['debug']:
    logger.setLevel(logging.DEBUG)

#database logger
#dblogger = logging.getLogger('sqlalchemy.engine')
#dblogger.setLevel(logging.INFO)
#_log_path = path.join(environ['inyoka_location'], 'db.log')
#dblogger.addHandler(logging.FileHandler(_log_path))
