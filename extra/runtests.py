#!/usr/bin/env python
"""
    Inyoka Testrunner
    ~~~~~~~~~~~~~~~~~

    Note, that running the tests is not available via manage-inyoka.py, cause
    we import some stuff there and that does kill covergae.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import nose

import coverage
coverage.erase()
coverage.coverage(auto_data=True, branch=True)
coverage.start()

from inyoka.application import InyokaApplication
application = InyokaApplication('inyoka_tests.ini')

from inyoka.core.api import config, environ
from inyoka.core.test import InyokaPlugin
from inyoka.core import database

def run_suite(module='inyoka'):
    from os import path

    # initialize the app

    tests_path = path.join(environ.PACKAGE_LOCATION, 'tests')

    trans = config.edit()
    trans['database_debug'] = True
    trans['debug'] = True
    config.touch()

    import nose.plugins.builtin
    plugins = [InyokaPlugin()]

    config['debug'] = True
    engine = database.get_engine()
    # first we cleanup the existing database
    database.metadata.drop_all(bind=engine)
    # then we create everything
    database.init_db(bind=engine)
    try:
        nose.run(addplugins=plugins, module=module)
    finally:
        # and at the end we clean up our stuff
        database.metadata.drop_all(bind=engine)



if __name__ == '__main__':
    run_suite()
