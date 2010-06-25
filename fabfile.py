#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Fabfile
    ~~~~~~~

    Our makefile replacement with `Fabric <http://fabfile.org>`_.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from __future__ import with_statement
import os
import sys
from os import path as _path, access, F_OK
from functools import partial as _partial
from fabric.api import *


# setup PYTHONPATH and current sys.path
_base_dir = _path.realpath(_path.join(_path.dirname(__file__)))
sys.path.append(_base_dir)
_python_path = os.environ.get('PYTHONPATH', '')
os.environ['PYTHONPATH'] = os.pathsep.join((_base_dir, _python_path))
#: partial function that is used for easy absolute path usage
#: to make the fabfile more useful if you're not in the root folder
#: but need to do a `fab runserver` or something else.
_j = lambda *a: _path.join(_base_dir, *a)


def _make_app(cfg='inyoka.ini', debug=False, profile=False, leaky=False):
    cfg = os.environ.setdefault('INYOKA_CONFIG', cfg)
    from inyoka.core.api import ctx
    from flickzeug import debug as debugger, leakfinder, profiling
    dispatcher = ctx.dispatcher
    if debug:
        dispatcher = debugger.DebuggedApplication(dispatcher, evalex=True,
            show_hidden_frames=True)
    if profile:
        if not os.path.exists('profiles'):
            os.mkdir('profiles')
        dispatcher = profiling.Profiler(dispatcher, 'profiles')
    if leaky:
        dispatcher = leakfinder.LeakFinder(dispatcher, async_ajax=True)
    return dispatcher


def initdb():
    """Initialize the database"""
    dispatcher = _make_app()
    from inyoka.core.database import init_db, get_engine
    init_db(bind=get_engine())


def reset():
    """Reset the database and create new test data"""
    from inyoka.core.api import db
    db.metadata.drop_all(bind=db.get_engine())
    initdb()
    local("python %s" % _j('extra/create_testdata.py'), capture=False)


def _action(*args, **kwargs):
    def _inner(app_factory, hostname=None, port=None,
               threaded=False, processes=1):
        from werkzeug.serving import run_simple
        from inyoka.core.api import ctx

        parts = ctx.cfg['base_domain_name'].split(':')
        if hostname is None:
            hostname = parts[0]
        if port is None:
            port = int(parts[1])

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


def runeventlet(hostname='localhost', port=5000):
    """
    Run development server with Eventlet.
    """
    from eventlet import api, wsgi
    app = _make_app(debug=True)
    wsgi.server(api.tcp_listener((hostname, port)), app)


def runcherrypy(hostname='localhost', port=5000):
    """
    Run development server with CherryPy.
    """
    from cherrypy.wsgiserver import CherryPyWSGIServer
    from inyoka.core.api import ctx
    app = _make_app(debug=True)
    server = CherryPyWSGIServer((hostname, port), app,
        server_name=ctx.cfg['base_domain_name'])
    server.start()


def shell(app='ipython', banner=u'Interactive Inyoka Shell'):
    """Spawn a new interactive python shell

    :param app: choose between common python shell, ipyhon or bpython.
                Possible values are: python, ipython and bpython.
    """
    from code import interact
    namespace = {}
    assert app in ('python', 'ipython', 'bpython'), u'Your shell is not supported!'
    try:
        if app == 'python':
            interact(banner, local=namespace)
        elif app == 'ipython':
            import IPython
            sh = IPython.Shell.IPShellEmbed(banner=banner)
            sh(global_ns={}, local_ns=namespace)
        elif app == 'bpython':
            from bpython import embed
            embed(locals_=namespace, args=['-i', '-q'])
        else:
            raise ImportError()
    except ImportError:
        # fallback to default python interpreter
        from code import interact
        interact(banner, local=namespace)

def version():
    """
    Get Inyoka and Python version.
    """
    from inyoka import INYOKA_REVISION
    print u'Inyoka revision %s on Python %s' % \
          (INYOKA_REVISION, u'.'.join(str(x) for x in sys.version_info[:3]))

def celeryd():
    """
    Start a celery worker, using our config.
    """
    # the inyoka celery loader is temporarily deactivated until we have worked
    # over our import system.
    # local('CELERY_LOADER="inyoka.core.celery_support.CeleryLoader" celeryd --loglevel=INFO', capture=False)
    local('CELERY_LOADER="celery.loaders.default.Loader" celeryd --loglevel=INFO', capture=False)


def build_docs(clean='no', browse='no', builder='html'):
    """
    Generate the Sphinx documentation.  Possible builders:
    html, singlehtml, text, man, htmlhelp, qthelp, epub, changes.

    Use 'doctest' to run our doctests included in our documentation.

    This supports theoretically all builders supported by sphinx.
    """
    if clean.lower() in ['yes', 'y']:
        local('rm -r -f docs/_build/')
    with cd(_j('docs')):
        source, out = _j('docs/source'), _j('docs/_build/%s' % builder)
        cmd = ('sphinx-build -b %s -c %s -d %s %s %s' % (
            builder, _j('docs'), _j('docs/_build/doctrees'), source, out
        ))
        local(cmd, capture=False)
        print 'Build finished. The %s pages are in %s.' % (builder, out)
    if browse.lower() in ['yes', 'y']:
        local('open docs/_build/html/index.html')


def build_test_venv(pyver=None):
    """
    Create a virtual environment (for compatiblity).
    """
    create_virtualenv(pyver=pyver)


def create_virtualenv(directory='../inyoka-testsuite',pyver=None):
    """
    Create a virtual environment for inyoka.

    :param directory: Where to create this virtual environment (folder must not exist).
    :param pyver: Which Python Version to use.
    """
    if pyver is None:
        pyver = u'.'.join(str(x) for x in sys.version_info[:2])
    local('python %s -p %s > %s' % (_j('extra/make-bootstrap.py'),
          pyver, _j('bootstrap.py')), capture=False)
    local('python ./bootstrap.py -r %s %s' % (
        _j('requirements.txt'), directory), capture=False)


def clean_files():
    """
    Cleanup some Backup files and many more.
    """
    local("find . -name '*.pyc' -delete")
    local("find . -name '*.pyo' -delete")
    local("find . -name '*~' -delete")
    local("find . -name '*.orig' -delete")
    local("find . -name '*.orig.*' -delete")
    local("find . -name '*.py.fej' -delete")
    local("find . -name '*.egg' -delete")
    if access('bootstrap.py', F_OK):
        local("rm bootstrap.py")


def i18n():
    """
    Build i18n support.
    """
    local("python %s" % _j("extra/extract-messages"), capture=False)
    local("python %s" % _j("extra/update-translations"), capture=False)
    local("python %s" % _j("extra/compile-translations"), capture=False)


def test(file='', clean='yes'):
    """
    Run all unit tests and doctests.

    Specify clean=no if you don't want to remove old .coverage/.noseid files.
    To only run tests from specific files, use test:tests/foo/test_bar.py,
    separate multiple files by spaces (don't forget to escape it on the shell)
    """

    clean = True if clean == 'yes' else False
    def _clean():
        try:
            clean_files()
            os.unlink('.coverage')
            os.unlink('.noseids')
        except OSError:
            pass

    if clean:
        with settings(hide('running')):
            _clean()

    local('python %s %s' % (_j('extra/runtests.py'), file), capture=False)


def reindent():
    """
    Reindents the sources.
    """
    local(_j('extra/reindent.py -r -B %s' % _base_dir), capture=False)

def lsdns():
    """
    Get the required DNS settings.
    """
    from urllib2 import splitport
    from inyoka.core.api import ctx

    print u' '.join((sub +'.' if sub else sub) + splitport(ctx.dispatcher.url_adapter.server_name)[0] for sub in sorted(set(rule.subdomain for rule in ctx.dispatcher.url_map.iter_rules())))
