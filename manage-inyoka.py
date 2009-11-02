#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Inyoka Management Script
    ~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sys
from werkzeug import script


def make_app():
    from inyoka.application import application
    return application


def make_shell():
    application = make_app()
    return locals()


def action_runtests(cleanup=True, debug=True):
    """Run the unit and doctests"""
    import sys
    from os import path
    from werkzeug import import_string

    # initialize the app
    from inyoka.application import application

    from inyoka.core.api import config, environ

    tests_path = path.join(environ.PACKAGE_LOCATION, 'tests')
    #TODO: support other databases for unittests
    sqlite_path = path.join(tests_path, 'test_database.db')
    dburi = 'sqlite:///%s' % sqlite_path

    trans = config.edit()
    trans['database_debug'] = debug
    trans['debug'] = debug
    config.touch()

    # remove unused options from sys.argv
    sys.argv = sys.argv[:1]

    from inyoka.core.test import run_suite
    run_suite(tests_path, cleanup)

def make_runserver():
    # initialize the app
    from inyoka.application import application
    from inyoka.core.api import config
    parts = config['base_domain_name'].split(':')
    port = int(parts[1]) if len(parts) == 2 else 80
    return script.make_runserver(make_app, port=port, use_reloader=True,
                                 use_debugger=True, use_evalex=True)

action_shell = script.make_shell(make_shell, 'Interactive Inyoka Shell')
# TODO make configureable
action_runserver = make_runserver()


def print_version():
    from inyoka import INYOKA_REVISION
    print 'Inyoka revision %s on Python %s' % \
          (INYOKA_REVISION, sys.version.replace('\n', 'compiled with '))


def main():
    args = sys.argv[1:]
    if '--version' in args or '-v' in args:
        return print_version()
    script.run(globals(), args=args)

if __name__ == '__main__':
    main()
