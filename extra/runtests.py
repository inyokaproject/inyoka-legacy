#!/usr/bin/env python
"""
    Inyoka Testrunner
    ~~~~~~~~~~~~~~~~~

    Note, that running the tests is not available via manage-inyoka.py, cause
    we import some stuff there and that does kill coverage.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import nose, sys, os

import coverage
coverage.erase()
coverage.exclude('#pragma[: ]+[nN][oO] [cC][oO][vV][eE][rR]')
coverage.coverage(auto_data=True, branch=True)
coverage.start()

# set the configuration file
os.environ['INYOKA_CONFIG'] = 'inyoka_tests.ini'
# we need to setup the inyoka application at this time
# to setup the thread local cache properly
from inyoka.application import InyokaApplication
application = InyokaApplication()

from inyoka.core.api import config
from inyoka.core.test import InyokaPlugin
from inyoka.core.database import refresh_engine


def run_suite(module='inyoka'):
    from os import path

    # initialize the app

    tests_path = path.join(os.environ['INYOKA_INSTANCE'], 'tests')

    # force the engine to be bound to the new database
    refresh_engine()

    plugins = [InyokaPlugin()]

    nose.main(addplugins=plugins, module=module)


if __name__ == '__main__':
    sys.exit(run_suite())
