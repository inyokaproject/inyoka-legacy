# -*- coding: utf-8 -*-
"""
    inyoka.core.test
    ~~~~~~~~~~~~~~~~

    This module abstracts nosetest and provides an interface for our unittests
    and doctests.  It also implements various helper classes and functions.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os, sys
import unittest
import warnings
import functools

import nose
import nose.tools
from nose.plugins import cover, base

from werkzeug import Client
from werkzeug.contrib.testtools import ContentAccessors
from minimock import mock, Mock, TraceTracker, restore as revert_mocks

from inyoka.core import database
from inyoka.core.database import db
from inyoka.core.context import current_application, local, config
from inyoka.core.http import Response
from inyoka.core.templating import TEMPLATE_CONTEXT
from inyoka.utils.logger import logger
from inyoka.utils.urls import make_full_domain


# disable the logger
logger.disabled = True

warnings.filterwarnings('ignore', message='lxml does not preserve')
warnings.filterwarnings('ignore', message=r'object\.__init__.*?takes no parameters')

__all__ = ('TestResponse', 'ViewTestCase', 'fixture', 'with_fixtures', 'future',
           'tracker', 'mock', 'Mock', 'revert_mocks', 'db', 'Response', 'config')
__all__ = __all__ + tuple(nose.tools.__all__)

dct = globals()
for obj in nose.tools.__all__:
    dct[obj] = getattr(nose.tools, obj)

# an overall trace tracker from minimock
tracker = TraceTracker()


class TestResponse(Response, ContentAccessors):
    """Responses for the test client."""


class ViewTestCase(unittest.TestSuite):

    controller = None

    def _pre_setup(self):
        """Performs any pre-test setup. This includes:

            * install the test client
            * set up the base url and base domain values
        Note that this method is called right *before*
        fixtures and such stuff are set up.
        """
        #TODO: are fixtures required here or in the InyokaPlugin?
        self._client = Client(current_application, response_wrapper=TestResponse)
        self.base_domain = config['base_domain_name']
        name = self.controller.name
        subdomain, submount = config['routing.urls.' + name].split(':', 1)
        self.base_url = make_full_domain(subdomain)

    def _post_teardown(self):
        """Performs any post-test things.

        Note that this methdod is called right *before*
        the internal test suite cleans up it's trash.  So you
        can still access the fixtures and other things here.
        """
        return

    def get_context(self, path, method='GET', **kwargs):
        ret = self.open(path, method=method, **kwargs)
        return TEMPLATE_CONTEXT

    def open(self, path, *args, **kw):
        app = local.application
        if 'follow_redirects' not in kw:
            kw['follow_redirects'] = True
        kw['base_url'] = self.base_url
        kw['buffered'] = True
        response = self._client.open(path, *args, **kw)

        app.bind()
        return response

    def get(self, *args, **kw):
        """Like open but method is enforced to GET."""
        kw['method'] = 'GET'
        return self.open(*args, **kw)

    def post(self, *args, **kw):
        """Like open but method is enforced to POST."""
        kw['method'] = 'POST'
        return self.open(*args, **kw)

    def normalize_local_path(self, path):
        if path in ('', '.'):
            path = path
        elif path.startswith(self.base_url):
            path = path[len(self.base_url) - 1:]
        return path

    def submit_form(self, path, data, follow_redirects=False):
        response = self.get(path)
        try:
            form = response.lxml.xpath('//form')[0]
        except IndexError:
            raise RuntimeError('no form on page')
        csrf_token = form.xpath('//input[@name="_csrf_token"]')[0]
        data['_csrf_token'] = csrf_token.attrib['value']
        action = self.normalize_local_path(form.attrib['action'])
        return self.post(action, method=form.attrib['method'].upper(),
                                data=data, follow_redirects=follow_redirects)


class InyokaPlugin(cover.Coverage):
    """Nose plugin extension

    This prevents modules from being loaded without a configured Inyoka
    environment.

    """
    enabled = False
    enableOpt = 'inyoka_config'
    name = 'inyoka'
    _started = False

    def options(self, parser, env):
        # Don't setup coverage options,
        # base.Plugin takes care of with-inyoka
        base.Plugin.options(self, parser, env)

    def begin(self):
        """We overwrite this method to push in our database
        setup and to not setup coverage again, since we start it
        quite a lot earlier.
        """
        self._engine = engine = database.get_engine()
        # first we cleanup the existing database
        database.metadata.drop_all(bind=engine)
        # then we create everything
        database.init_db(bind=engine)

        self.skipModules = [i for i in sys.modules.keys() if not i.startswith('inyoka')]

    def finalize(self, result):
        database.metadata.drop_all(bind=self._engine)

    def configure(self, options, conf):
        """Configure the plugin"""
        self.config_file = None
        self.conf = conf
        self.coverInclusive = True
        self.coverHtmlDir = os.environ.get('NOSE_COVER_HTML_DIR', '.coverage_html')
        self.coverPackages = ['inyoka']
        if hasattr(options, self.enableOpt):
            self.enabled = bool(getattr(options, self.enableOpt))
            self.config_file = getattr(options, self.enableOpt)

    def startTest(self, test):
        """Called before each test seperately to support our
        own fixture system.

        Note that this is called for *each* test *method* not
        every TestCase.
        """
        t = test.test

        if isinstance(t, nose.case.MethodTestCase):
            # enable our test suite to setup internal things
            t.inst._pre_setup()

        # setup the new transaction context so that we can revert
        # it to get a clean and nice database
        self._connection = conn = self._engine.connect()
        self._transaction = trans = conn.begin()
        db.session.bind = conn

        if hasattr(t, 'test') and hasattr(t.test, '_required_fixtures'):
            self._started = True
            # reset the database data.  That way we can assure
            # that we get a clear database
            for fixture in t.test._required_fixtures:
                functions = test.context.fixtures[fixture]
                instances = [func() for func in functions]
                db.session.add_all(instances)
                db.session.commit()

    def stopTest(self, test):
        if self._started:
            self._started = False
            if isinstance(test.test, nose.case.MethodTestCase):
                test.test.inst._post_teardown()

        # revert all mock objects to get clear passage on the next test
        revert_mocks()
        # rollback the transaction
        db.session.commit()
        db.session.close()
        self._transaction.rollback()

    def wantClass(self, cls):
        # we want view test cases to be loaded with no matter
        # if they are
        if issubclass(cls, ViewTestCase):
            return True
        else:
            return False

    def report(self, stream):
        """
        Output code coverage report.
        """
        import coverage
        coverage.stop()
        modules = [ module
                    for name, module in sys.modules.items()
                    if self.wantModuleCoverage(name, module) ]
        html_reporter = coverage.html.HtmlReporter(coverage._the_coverage)
        if self.coverHtmlDir:
            if not os.path.exists(self.coverHtmlDir):
                os.makedirs(self.coverHtmlDir)
            html_reporter.report(modules, self.coverHtmlDir)


#TODO: write unittests
def fixture(model, _callback=None, **kwargs):
    """Insert some test fixtures into the database"""
    def onload():
        if _callback is not None:
            data = _callback()
        kwargs.update(data)
        table = model.__table__
        names = [col for col in kwargs.keys()]
        m = model(**kwargs)
        return m
    return onload


def with_fixtures(*names):
    def proxy(func):
        func._required_fixtures = names
        return func
    return proxy


#TODO: write unittests
def future(func):
    """Mark a test as expected to unconditionally fail."""
    fn_name = func.func_name
    @functools.wraps(func)
    def future_decorator(*args, **kw):
        try:
            func(*args, **kw)
        except Exception, ex:
            print ("Future test '%s' failed as expected: %s " % (
                fn_name, str(ex)))
            return True
        else:
            raise AssertionError(
                "Unexpected success for future test '%s'" % func.func_name)
    return future_decorator
