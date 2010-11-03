# -*- coding: utf-8 -*-
"""
    inyoka.core.celery_support
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Support module for celery.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from celery.loaders.base import BaseLoader
from celery.loaders.default import AttributeDict

from inyoka.context import ctx
from inyoka.core.config import TextConfigField, ListConfigField, IntegerConfigField


# celery broker settings
celery_result_backend = TextConfigField('celery.result_backend', default=u'amqp')
celery_result_dburi = TextConfigField('celery.result_dburi', default=u'sqlite://')
celery_imports = ListConfigField('celery.imports', default=['inyoka.core.tasks'])
celery_task_serializer = TextConfigField('celery.task_serializer', default='pickle')

# ampq broker settings
broker_host = TextConfigField('broker.host', u'localhost')
broker_port = IntegerConfigField('broker.port', 5672)
broker_user = TextConfigField('broker.user', u'inyoka')
broker_password = TextConfigField('broker.password', u'default')
broker_vhost = TextConfigField('broker.vhost', u'inyoka')


class CeleryLoader(BaseLoader):
    """A customized celery configuration loader that implements a bridge
    between :mod:`inyoka.core.config` and the celery configuration system.
    """

    def read_configuration(self):
        """Read the configuration from configuration file and convert values
        to celery processable values."""
        celeryd_vars = list(ctx.cfg.itersection('celeryd'))
        celery_vars = list(ctx.cfg.itersection('celery'))
        broker_vars = list(ctx.cfg.itersection('broker'))

        conv = lambda x: (x[0].upper().replace('.','_'),x[1])

        settings = map(conv, celeryd_vars + celery_vars + broker_vars)
        settings.append(('DEBUG', ctx.cfg['debug']))
        settings.append(('CELERY_ALWAYS_EAGER', ctx.cfg['testing']))
        self.configured = True

        return AttributeDict(dict(settings))

    def on_worker_init(self):
        """Imports modules at worker init so tasks can be registered
        and used by the worked.

        The list of modules to import is taken from the ``celery.imports``
        configuration value.
        """
        self.import_default_modules()
