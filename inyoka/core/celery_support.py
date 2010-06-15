# -*- coding: utf-8 -*-
"""
    inyoka.core.celery
    ~~~~~~~~~~~~~~~~~~

    Support module for celery.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from celery.loaders.base import BaseLoader
from celery.loaders.default import Settings

from inyoka.core.context import ctx

class CeleryLoader(BaseLoader):
    def read_configuration(self):
        celeryd_vars = list(ctx.cfg.itersection('celeryd'))
        celery_vars = list(ctx.cfg.itersection('celery'))
        broker_vars = list(ctx.cfg.itersection('broker'))

        conv = lambda x: (x[0].upper().replace('.','_'),x[1])

        settings = map(conv, celeryd_vars + celery_vars + broker_vars)
        settings.append(('DEBUG', ctx.cfg['debug']))
        self.configured  = True

        return Settings(settings)

    def on_worker_init(self):
        """Imports modules at worker init so tasks can be registered
        and used by the worked.

        The list of modules to import is taken from the ``CELERY_IMPORTS``
        setting in ``celeryconf.py``.
        """
        self.import_default_modules()

