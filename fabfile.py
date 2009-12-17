# -*- coding: utf-8 -*-
"""
    Fabfile
    ~~~~~~~

    Our makefile replacement with `Fabric <http://fabfile.org>`_.

    :copyright: 2009 by the Inyok Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from __future__ import with_statement
import os
import sys
from os import path as _path
from functools import partial as _partial
from fabric.api import *
from flickzeug import debug as _debug, leakfinder as _leakfinder, \
    profiling as _profiling


# setup PYTHONPATH and current sys.path
_base_dir = _path.realpath(_path.join(_path.dirname(__file__)))
sys.path.append(_base_dir)
_python_path = os.environ.get('PYTHONPATH', '')
os.environ['PYTHONPATH'] = os.pathsep.join((_base_dir, _python_path))


def _make_app(cfg='inyoka.ini', debug=False, profile=False, leaky=False):
    os.environ['INYOKA_CONFIG'] = cfg
    from inyoka.application import InyokaApplication
    application = InyokaApplication()
    if debug:
        application = _debug.DebuggedApplication(application, evalex=True,
            show_hidden_frames=True)
    if profile:
        if not os.path.exists('profiles'):
            os.mkdir('profiles')
        application = _profiling.Profiler(application, 'profiles')
    if leaky:
        application = _leakfinder.LeakFinder(application, async_ajax=True)
    return application


def initdb():
    """Initialize the database"""
    application = _make_app()
    from inyoka.core.database import init_db, get_engine
    init_db(bind=get_engine())


def _action(*args, **kwargs):
    def _inner(app_factory, hostname='localhost', port=5000, threaded=False, processes=1):
        from werkzeug.serving import run_simple
        from inyoka.core.api import config
        parts = config['base_domain_name'].split(':')
        port = int(parts[1]) if len(parts) == 2 else port
        app = app_factory()
        run_simple(hostname, port, app, threaded=threaded,
            processes=processes, use_reloader=True, use_debugger=False)
    return _partial(_inner, *args, **kwargs)


runserver = _action(lambda: _make_app(debug=True))
runserver.__doc__ = u'Run a development server'
profiled = _action(lambda: _make_app(debug=True, profile=True))
profiled.__doc__ = u'Run a development server with activated profiler.'
leakfinder = _action(lambda: _make_app(debug=True, leaky=True))
leakfinder.__doc__ = u'Run a development server with activated leakfinder.'


def shell(use_ipython=True, banner=u'Interactive Inyoka Shell'):
    """Spawn a new interactive python shell"""
    namespace = {}
    try:
        import IPython
    except ImportError:
        pass
    else:
        sh = IPython.Shell.IPShellEmbed(banner=banner)
        sh(global_ns={}, local_ns=namespace)
        return
    from code import interact
    interact(banner, local=namespace)


def version():
    from inyoka import INYOKA_REVISION
    print u'Inyoka revision %s on Python %s' % \
          (INYOKA_REVISION, u'.'.join(str(x) for x in sys.version_info[:3]))


def runtests(args=None):
    """
    Run all unit tests and doctests.

    Specify string argument ``args`` for additional args to ``nosetests``.
    """
    if args is None:
        args = ""
    print(local('python extra/runtests.py %s' % args, capture=False))


def build_docs(clean='no', browse='no'):
    """
    Generate the Sphinx documentation.
    """
    c = ""
    if clean.lower() in ['yes', 'y']:
        c = "clean "
    b = ""
    if browse.lower() in ['yes', 'y']:
        b = " && open _build/html/index.html"
    local('cd docs; make %shtml%s' % (c, b), capture=False)


def build_test_venv(pyver=None):
    if pyver is None:
        pyver = u'.'.join(str(x) for x in sys.version_info[:2])
    local('python extra/make-bootstrap.py %s > ../bootstrap.py' % pyver,
          capture=False)
    local('cd .. && python bootstrap.py inyoka-testsuite', capture=False)


def clean_files():
    local("find . -name '*.pyc' -delete")
    local("find . -name '*.pyo' -delete")
    local("find . -name '*~' -delete")
    local("find . -name '*.orig' -delete")
    local("find . -name '*.orig.*' -delete")
    local("find . -name '*.py.fej' -delete")


def i18n():
    local("python extra/extract-messages", capture=False)
    local("python extra/update-translations", capture=False)
    local("python extra/compile-translations", capture=False)


def test():
    local("extra/buildbottest.sh %s" % os.getcwd(), capture=False)


def reindent():
    local("extra/reindent.py -r -B .", capture=False)


def help(command=None):
    from fabric.main import list_commands, display_command
    if command is not None:
        display_command(command)
    else:
        list_commands()
