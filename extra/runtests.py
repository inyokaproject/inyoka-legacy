#!/usr/bin/env python
"""
    Inyoka Testrunner
    ~~~~~~~~~~~~~~~~~

    Note, that running the tests is not available via manage-inyoka.py, cause
    we import some stuff there and that does kill coverage.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import nose, os

import coverage
coverage.erase()
coverage.exclude('#pragma[: ]+[nN][oO] [cC][oO][vV][eE][rR]')
coverage.coverage(auto_data=True, branch=True)
coverage.start()

# set the configuration file
os.environ['INYOKA_CONFIG'] = 'inyoka_tests.ini'
from inyoka.core.test import InyokaPlugin, FuturePlugin
from inyoka.core.database import refresh_engine


def run_suite(module='inyoka'):
    from os import path

    # initialize the app
    tests_path = path.join(os.environ['INYOKA_INSTANCE'], 'tests')

    # We need debug set to True for our tests
    from inyoka.core.context import ctx
    ctx.cfg['debug'] = 1

    # force the engine to be bound to the new database
    refresh_engine()

    plugins = [InyokaPlugin(), FuturePlugin()]

    nose.main(addplugins=plugins, module=module)


if __name__ == '__main__':
    run_suite()
