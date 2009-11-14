#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Inyoka Management Script
    ~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import sys
from werkzeug import script
from flickzeug import debug as fdebug, leakfinder, profiling


def make_app(cfg='inyoka.ini', debug=False, profile=False, leaky=False):
    from inyoka.application import InyokaApplication
    application = InyokaApplication(cfg)
    if debug:
        application = fdebug.DebuggedApplication(application, evalex=True,
            show_hidden_frames=True)
    if profile:
        if not os.path.exists('profiles'):
            os.mkdir('profiles')
        application = profiling.Profiler(application, 'profiles')
    if leaky:
        application = leakfinder.LeakFinder(application, async_ajax=True)
    return application


def make_shell():
    application = make_app()
    return locals()

def action_initdb():
    application = make_app()
    from inyoka.core.database import init_db
    init_db()


def make_action(app_factory, hostname='localhost', port=5000,
                threaded=False, processes=1):
    from inyoka.core.api import config
    parts = config['base_domain_name'].split(':')
    port = int(parts[1]) if len(parts) == 2 else 80
    def action(hostname=('h', hostname), port=('p', port),
               threaded=threaded, processes=processes):
        """Start a new development server."""
        from werkzeug.serving import run_simple
        app = app_factory()
        run_simple(hostname, port, app, False, None, threaded, processes)
    return action


action_runserver = make_action(lambda: make_app(debug=True))
action_profiled = make_action(lambda: make_app(debug=True, profile=True))
action_leakfinder = make_action(lambda: make_app(debug=True, leaky=True))
action_shell = script.make_shell(make_shell, 'Interactive Inyoka Shell')


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
