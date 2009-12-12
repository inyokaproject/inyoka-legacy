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

from inyoka.application import InyokaApplication
application = InyokaApplication('inyoka_tests.ini')

from inyoka.core.api import config
from inyoka.core.test import InyokaPlugin
from inyoka.core.database import refresh_engine


def run_suite(module='inyoka'):
    from os import path

    # initialize the app

    tests_path = path.join(os.environ['package_folder'], 'tests')

    # force the engine to be bound to the new database
    refresh_engine()

    plugins = [InyokaPlugin()]

    nose.main(addplugins=plugins, module=module)


if __name__ == '__main__':
    sys.exit(run_suite())
