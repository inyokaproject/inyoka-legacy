#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Fabfile
    ~~~~~~~

    Our makefile replacement with `Fabric <http://fabfile.org>`_.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import sys
from os import path as _path, access as _access, mkdir as _mkdir, F_OK as _F_OK
from os.path import isdir as _isdir
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


def _make_app(cfg='inyoka.ini', debug=False):
    cfg = os.environ.setdefault('INYOKA_CONFIG', cfg)
    from inyoka.core.api import ctx
    from werkzeug.debug import DebuggedApplication
    dispatcher = ctx.dispatcher
    if debug:
        dispatcher = DebuggedApplication(dispatcher, evalex=True)
    return dispatcher


def initdb():
    """Initialize the database"""
    dispatcher = _make_app()
    from inyoka.core.database import init_db, get_engine
    init_db(bind=get_engine())


def reset(no_testdata=False):
    """Reset the database and create new test data"""
    from inyoka.core.api import db
    db.drop_all_tables()
    initdb()
    if not no_testdata:
        local("python %s" % _j('extra/create_testdata.py'), capture=False)


def _action(*args, **kwargs):
    def _inner(app_factory, hostname=None, port=None, server='simple'):
        from inyoka.core.api import ctx
        from inyoka.utils.urls import get_host_port_mapping, make_full_domain

        _hostname, _port = get_host_port_mapping(make_full_domain())[:-1]
        if hostname is None:
            hostname = _hostname
        if port is None:
            port = _port

        app = app_factory()

        def _simple():
            from werkzeug.serving import run_simple
            run_simple(hostname, port, app, threaded=False,
                processes=1, use_reloader=True, use_debugger=False)

        def _eventlet():
            from eventlet import api, wsgi
            wsgi.server(api.tcp_listener((hostname, port)), app)

        def _cherrypy():
            from cherrypy.wsgiserver import CherryPyWSGIServer
            server = CherryPyWSGIServer((hostname, port), app,
                server_name=ctx.cfg['base_domain_name'],
                request_queue_size=500)
            server.start()

        def _tornado():
            from tornado import httpserver, ioloop, wsgi
            container = wsgi.WSGIContainer(app)
            http_server = httpserver.HTTPServer(container)
            http_server.listen(port, hostname)
            ioloop.IOLoop.instance().start()

        def _gevent():
            from gevent import monkey; monkey.patch_all()
            from gevent.wsgi import WSGIServer
            WSGIServer((hostname, port), app).serve_forever()

        mapping = {
            'simple': _simple,
            'eventlet': _eventlet,
            'cherrypy': _cherrypy,
            'tornado': _tornado,
            'gevent': _gevent,
        }

        # run actually the server
        mapping[server]()
    return _partial(_inner, *args, **kwargs)


runserver = _action(lambda: _make_app(debug=True))
runserver.__doc__ = u'''Run a development server.
You can choose between Werkzeug (simple), eventlet, cherrypy or tornado
to run Inyoka.  Use the `server` attribute to set the server app'''


def shell(app='ipython', banner=u'Interactive Inyoka Shell'):
    """Spawn a new interactive python shell

    :param app: choose between common python shell, ipython or bpython.
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
    # we start celery with -B option to make periodic tasks possible
    cmd = ('CELERY_LOADER="inyoka.core.celery_support.CeleryLoader" '
           'celeryd --loglevel=INFO -B')
    local(cmd, capture=False)


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
        print 'Build finished. The %s pages are in %s' % (builder, out)
    if browse.lower() in ['yes', 'y']:
        local('open docs/_build/html/index.html')


def build_test_venv(pyver=None):
    """
    Create a virtual environment (for compatiblity).
    """
    create_virtualenv(pyver=pyver)


def create_virtualenv(directory=None, pyver=None, interpreter='python'):
    """
    Create a virtual environment for inyoka.

    :param directory: Where to create this virtual environment (folder must not exist).
    :param pyver: Which Python Version to use.
    """
    if directory is None:
        workon_home = os.environ.get('WORKON_HOME')
        if workon_home:
            directory = _path.join(workon_home, 'inyoka')
        else:
            directory = '../inyoka-testsuite'
    if not _isdir(directory):
        _mkdir(_path.expanduser(_path.expandvars(directory)))
    local('%s %s > %s' % (interpreter,
        _j('extra/make-bootstrap.py'), _j('bootstrap.py')), capture=False)
    local('%s ./bootstrap.py --no-site-packages -r %s %s' % (interpreter,
        _j('extra/requirements.txt'), directory), capture=False)


def clean_files():
    """Clean most temporary files"""
    for f in '*.py[co]', '*~', '*.orig', '*.rej':
        local("rm -rf `find -name '%s'|grep -v .hg`" % f)
    if _access('bootstrap.py', _F_OK):
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
    separate multiple files by spaces (don't forget to escape it on the shell).
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

    print u'Running unittests using %s' % os.environ.get('INYOKA_CONFIG', 'default config')
    local('python %s %s' % (_j('extra/runtests.py'), file),
          capture=False)

def doctest():
    build_docs(builder='doctest')


def reindent():
    """
    Reindents the sources.
    """
    local(_j('extra/reindent.py -r -B %s' % _base_dir), capture=False)


def lsdns(basedomain=None):
    """
    Get the required DNS settings.
    """
    from urllib2 import splitport
    from inyoka.core.api import ctx

    _old = ctx.cfg['base_domain_name']
    if basedomain is not None:
        ctx.cfg['base_domain_name'] = basedomain

    print u' '.join(((sub +'.' if sub else sub) +
                     splitport(ctx.dispatcher.get_url_adapter().server_name)[0])
        for sub in sorted(set(rule.subdomain
            for rule in ctx.dispatcher.url_map.iter_rules()))
    )

    ctx.cfg['base_domain_name'] = _old


def reindex(index):
    """
    Iterate over all documents we're able to find (even those that are already
    in the search index) and index them. Note that this may take a lot of time.
    """
    from xappy import errors
    from inyoka.core.resource import IResourceManager
    from inyoka.core.search import create_search_document

    index = IResourceManager.get_search_indexes()[index]

    # iterate over all search providers...
    for provider in index.providers.itervalues():
        # ... to get all their data
        for id, obj in provider.prepare_all():
            # create a new document for the search index
            doc = create_search_document('%s-%s' % (provider.name, id), obj)
            try:
                # try to create a new search entry
                index.indexer.add(doc)
            except errors.IndexerError:
                # there's already an exising one, replace it
                index.indexer.replace(doc)
        index.indexer.flush()
    index.indexer.close()


def search(index, query, count=50):
    """
    Search for `query` in the search index `index` and print `count` results.
    """
    from inyoka.core.resource import IResourceManager

    index = IResourceManager.get_search_indexes()[index]
    searcher = index.searcher

    query = searcher.query_parse(query, allow=index.direct_search_allowed)
    results = searcher.search(query, 0, int(count))

    for result in results:
        print u'%d. %s' % (result.rank, result.id)
