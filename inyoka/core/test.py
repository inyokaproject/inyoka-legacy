# -*- coding: utf-8 -*-
"""
    inyoka.core.test
    ~~~~~~~~~~~~~~~~

    This module abstracts nosetest and provides an interface for our unittests
    and doctests.  It also implements various helper classes and functions.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import sys
import unittest
import warnings
import functools

import nose
from nose.plugins import cover, base, errorclass

import twill

from werkzeug import Client, create_environ
from werkzeug.contrib.testtools import ContentAccessors
from minimock import mock, Mock, TraceTracker, restore as revert_mocks

from inyoka.l10n import parse_timestamp
from inyoka.context import ctx
from inyoka.core import database
from inyoka.core.database import db
from inyoka.core.http import Response, Request, get_bound_request
from inyoka.utils.logger import logger
from inyoka.utils.urls import make_full_domain, get_host_port_mapping


logger.disabled = True

warnings.filterwarnings('ignore', message='lxml does not preserve')
warnings.filterwarnings('ignore', message=r'object\.__init__.*?takes no parameters')

__all__ = ('TestResponse', 'ViewTestSuite', 'TestSuite', 'fixture', 'with_fixtures',
           'future', 'tracker', 'mock', 'Mock', 'revert_mocks', 'db', 'Response',
           'ctx', 'FixtureLoader')
__all__ = __all__ + tuple(nose.tools.__all__)

dct = globals()
for obj in nose.tools.__all__:
    dct[obj] = getattr(nose.tools, obj)
del dct

# an overall trace tracker from minimock
tracker = TraceTracker()


_iterables = (list, tuple, set, frozenset)


class TestResponse(Response, ContentAccessors):
    """Responses for the test client."""


class _TwillBrowserProxy(object):
    """Small twill browser proxy"""

    def __getattribute__(self, name):
        return getattr(twill.get_browser(), name)

    def __setattr__(self, name, value):
        setattr(twill.get_browser(), name, value)

# define shortcuts for twill
twill.b = _TwillBrowserProxy()
twill.c = twill.commands


# Fixture Framework
#
# The code is based on `bootalchemy <http://pypi.python.org/pypi/bootalchemy>`
# but was heavily modified to better match into Inyoka.


class FixtureLoader(object):
    """Basic fixture loader

    :references: References from a sqlalchemy session to initialize with.
    :check_types: Introspect the garget model to re-cast the data appropriately.
    """
    def __init__(self, references=None, check_types=True):
        if references is None:
            self._references = {}
        else:
            self._references = references

        self.check_types = check_types

    def clear(self):
        """
        clear the existing references
        """
        self._references = {}

    def create_obj(self, cls, item):
        """
        create an object with the given data
        """
        return cls(**item)

    def update_item(self, item):
        new_item = item.copy()
        for key, value in new_item.iteritems():
            if isinstance(value, basestring) and value.startswith('&'):
                new_item[key] = None
            if isinstance(value, basestring) and value.startswith('*'):
                id = value[1:]
                new_item[key] = self._references.get(id, new_item[key])
            if isinstance(value, list):
                l = []
                for i in value:
                    if isinstance(i, basestring) and i.startswith('*'):
                        id = i[1:]
                        l.append(self._references.get(id, i))
                        continue
                    l.append(i)
                new_item[key] = l
        return new_item

    def has_references(self, item):
        for key, value in item.iteritems():
            if isinstance(value, basestring) and value.startswith('&'):
                return True

    def add_reference(self, key, obj):
        """
        add a reference to the internal reference dictionary
        """
        self._references[key[1:]] = obj

    def set_references(self, obj, item):
        """
        extracts the value from the object and stores them in the reference dictionary.
        """
        for key, value in item.iteritems():
            if isinstance(value, basestring) and value.startswith('&'):
                self._references[value[1:]] = getattr(obj, key)
            if isinstance(value, list):
                for i in value:
                    if isinstance(value, basestring) and i.startswith('&'):
                        self._references[value[1:]] = getattr(obj, value[1:])

    def _check_types(self, cls, obj):
        if not self.check_types:
            return obj
        mapper = db.class_mapper(cls)
        for table in mapper.tables:
            for key in obj.keys():
                col = table.columns.get(key, None)
                if col is not None and isinstance(col.type, (db.Date, db.DateTime, db.Time)) \
                                   and isinstance(obj[key], basestring):
                    obj[key] = parse_timestamp(obj[key])
                    continue
                if col is not None and isinstance(col.type, (db.Unicode, db.String)) \
                                   and isinstance(obj[key], basestring):
                    obj[key] = unicode(obj[key])
                    continue
        return obj

    def from_list(self, session, data):
        """Extract data from a list of groups in the form:

        [{
            'User: [{
                'username': 'peter',
                'email': 'peter@example.com'
            }, {
                'username': 'Paul'
                'email': paul@example.com'
            }],
        }]

        """
        for group in data:
            for name, items in group.iteritems():
                if name in ('nocommit',):
                    continue

                # try to find the right model class
                cls = None
                models = list(db.ISchemaController.get_models())
                names = [m.__name__ for m in models]
                if name in names:
                    cls = models[names.index(name)]

                # check that the class was found.
                if cls is None:
                    raise AttributeError('Model %s not found' % name)

                for item in items:
                    ref_name = None
                    keys = item.keys()
                    if (len(keys) == 1 and keys[0].startswith('&') and \
                            isinstance(item[keys[0]], dict)):
                        ref_name = keys[0]
                        item = item[ref_name]
                        name = name[1:]
                    new_item = self.update_item(item)
                    new_item = self._check_types(cls, new_item)
                    obj = self.create_obj(cls, new_item)
                    session.add(obj)
                    if ref_name:
                        self.add_reference(ref_name, obj)
                    if self.has_references(item):
                        session.flush()
                        self.set_references(obj, item)
            keys = group.keys()
            if not 'nocommit' in keys:
                session.commit()

        # commit everything at the end of fixture loading
        session.commit()


class TestSuite(unittest.TestSuite):
    """TestSuite for the Inyoka test framework.

    A TestSuite holds various test methods for unittesting and
    is able to use our own fixtures framework.
    """

    #: dictionary full of fixtures
    fixtures = {}

    def _pre_setup(self):
        """Internal setup method so that unittests can implement setUp.

        Note that this method is called right *before*
        fixtures and such stuff are set up.
        """

    def _post_teardown(self):
        """Performs any post-test things.

        Note that this methdod is called right *before*
        the internal test suite cleans up it's trash.  So you
        can still access the fixtures and other things here.
        """


class ViewTestSuite(TestSuite):
    """A test case suitable to test view methods properly"""

    controller = None

    def _pre_setup(self):
        """Setup the test client and url and base domain values"""
        self.client = Client(ctx.dispatcher, response_wrapper=TestResponse,
                             use_cookies=True)
        self.base_domain = ctx.cfg['base_domain_name']
        name = 'test' if self.controller is None else self.controller.name
        subdomain = ctx.cfg['routing.urls.' + name].split(':', 1)[0]
        self.base_url = make_full_domain(subdomain)

        # twill integration.  This intercept forwards all twill commands
        # to our respective wsgi dispatcher
        host, port, scheme = get_host_port_mapping(self.base_domain)
        twill.add_wsgi_intercept(host, port, lambda: ctx.dispatcher)

    def _post_teardown(self):
        # remove the twill intercept
        host, port, scheme = get_host_port_mapping(self.base_domain)
        twill.remove_wsgi_intercept(host, port)

    def get_context(self, path, method='GET', **kwargs):
        """
        Return the template context from a view wrapped by :func:`templated`.
        """
        response = self.open(path, method=method, **kwargs)
        return getattr(response, '_template_context', {})

    def open(self, path, *args, **kw):
        """
        Open a connection to `path` and return the proper response object.

        If the @templated decorator was used, the template context is stored
        in the response objects's `_template_context` property.
        """
        if 'follow_redirects' not in kw:
            kw['follow_redirects'] = True
        kw['base_url'] = self.base_url
        kw['buffered'] = True
        response = self.client.open(path, *args, **kw)
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
        """Simple local path normalizing.

        This checks for absolute uris and makes them local.
        """
        if path in ('', '.'):
            path = path
        elif path.startswith(self.base_url):
            path = path[len(self.base_url) - 1:]
        return path

    def submit_form(self, path, data, follow_redirects=False):
        """Submit a form to `path` with `data`

        :param path: The path to query.
        :param data: A dictionary containing the form data.
        :param follow_redirects: Follow redirects.
        """
        response = self.get(path)
        try:
            form = response.lxml.xpath('//form')[0]
        except IndexError:
            raise RuntimeError('no form on page')
        csrf_token = form.xpath('//input[@name="csrf_token"]')[0]
        data.setdefault('csrf_token', csrf_token.attrib['value'])
        action = self.normalize_local_path(form.attrib['action'])
        return self.post(action or path, method=form.attrib['method'].upper(),
                                data=data, follow_redirects=follow_redirects)

    def get_new_request(self, *args, **kwargs):
        """Creates a WSGI environment from the given values (see
        :func:`werkzeug.create_environ` for more information, this
        function accepts the same arguments).
        """
        kwargs['base_url'] = self.base_url
        req = get_bound_request(ctx.dispatcher.request_class,
                                create_environ(*args, **kwargs))
        return req

    # Advanced Unittest methods for easy unittests

    def assertRedirects(self, response, location):
        assert response.status_code in (301, 302)
        assert response.location == os.path.join(self.base_url, location)

    def assertStatus(self, response, status_code):
        eq_(response.status_code, status_code)

    def assertResponseOK(self, response):
        self.assertStatus(response, 200)

    def assertNotFound(self, response):
        self.assertStatus(response, 404)

    def assertHeader(self, response, key, value=None):
        """Fail if (key, [value]) not in response.headers"""
        ikey = key.lower()
        values = response.headers.getlist(ikey)
        if values and value is None or value in values:
            return True

        if value is None:
            msg = u'%r not in headers' % key
        else:
            msg = '%r:%r not in headers' % (key, value)
        raise AssertionError(msg)

    def assertNoheader(self, response, key):
        """Fail if key in response.headers"""
        if key.lower() in response.headers:
            raise AssertionError(u'%r in headers' % key)
        return True

    def assertContext(self, response, value):
        tctx = getattr(response, '_template_context', {})
        if value != tctx:
            raise AssertionError(u'Expected context:\n%r\n\nActual Context:\n%r'
                                 % (value, tctx))
        return True

    def make_twill_url(self, url):
        return u'%s://%s:%d%s' % (get_host_port_mapping(self.base_domain), url)



class InyokaPlugin(cover.Coverage):
    """Nose plugin extension

    This plugin prevents modules from being loaded without a configured
    Inyoka environment.

    It also implements our fixture system and fixes the coverage html output.

    """

    enabled = False
    enableOpt = 'inyoka_config'
    name = 'inyoka'
    _started = False

    def __init__(self):
        super(InyokaPlugin, self).__init__()
        # Force our `tests` module to be the first `tests` module in the path.
        # Otherwise load_packages might try to load `test` from celery if
        # installed via setup.py develop (same goes for other packages)
        sys.path.insert(0, os.path.dirname(os.environ['INYOKA_MODULE']))
        ctx.load_packages(['tests.*'])

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

        # connect to the engine
        self._connection = conn = self._engine.connect()
        db.session.bind = conn

        self.skipModules = [i for i in sys.modules.keys() if not i.startswith('inyoka')]

    def finalize(self, result):
        """Finally drop all database tables."""
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
        own fixture system and call special initialisation methods.

        Note that this is called for *each* test *method* not
        every TestCase.
        """
        t = test.test

        if isinstance(t, nose.case.MethodTestCase):
            # enable our test suite to setup internal things
            t.inst._pre_setup()

        # setup the new transaction context so that we can revert
        # it to get a clean and nice database
        self._transaction = self._connection.begin()

        if hasattr(t, 'test') and hasattr(t.test, '_required_fixtures'):
            self._started = True
            # reset the database data.  That way we can assure
            # that we get a clear database
            loaded = {}
            for fixture in t.test._required_fixtures:
                loader = test.context.fixtures[fixture]
                try:
                    if isinstance(loader, _iterables):
                        instances = []
                        for func in loader:
                            value = func()
                            db.session.add(value)
                            db.session.commit()
                            instances.append(value)
                    else:
                        instances = loader()
                        to_load = instances if isinstance(instances, _iterables) \
                                    else [instances]
                        db.session.add_all(to_load)
                    loaded[fixture] = instances
                except db.SQLAlchemyError:
                    db.session.rollback()
                    raise
            t.test = functools.partial(t.test, loaded)

    def stopTest(self, test):
        """Called after each test seperately to clear up fixtures as
        well as mock objects.

        This also calls all cleanup callbacks for the WSGI Dispatcher.

        Note that this is called for *each* test *method* not
        every TestCase.
        """
        if self._started:
            self._started = False
            if isinstance(test.test, nose.case.MethodTestCase):
                test.test.inst._post_teardown()

        # revert all mock objects to get clear passage on the next test
        revert_mocks()
        try:
            db.session.close()
        except db.SQLAlchemyError:
            db.session.rollback()
            raise
        # rollback the transaction
        self._transaction.rollback()
        for callback in ctx.dispatcher.cleanup_callbacks:
            callback()

    def wantClass(self, cls):
        """Check if we can use a `cls` for unittest purposes.  This adds
        `ViewTestSuite` to the list of possible unittest interfaces."""
        if issubclass(cls, ViewTestSuite) and not cls is ViewTestSuite:
            return True
        if cls is ViewTestSuite:
            return False
        return None

    def wantFile(self, file):
        """Exclude `fabfile.py` explicitly from unittests"""
        if 'fabfile.py' in file:
            return False
        return cover.Coverage.wantFile(self, file)

    def report(self, stream):
        """
        Output code coverage report.
        """
        import coverage
        coverage.stop()
        modules = [module for name, module in sys.modules.items()
                   if self.wantModuleCoverage(name, module)]
        html_reporter = coverage.html.HtmlReporter(coverage._the_coverage)
        if self.coverHtmlDir:
            if not os.path.exists(self.coverHtmlDir):
                os.makedirs(self.coverHtmlDir)
            html_reporter.report(modules, self.coverHtmlDir)


#TODO: write unittests
def fixture(model, _callback=None, **kwargs):
    """Insert some test fixtures into the database"""
    def onload():
        data = {}
        if _callback is not None:
            data = _callback if isinstance(_callback, dict) else _callback()
        kwargs.update(data)
        m = model(**kwargs)
        return m
    return onload


def with_fixtures(*names):
    """Mark this function to work with some fixture.

    Example usage::

        class MyTest(TestSuite):
            fixtures = {'fix1': fixture(Entry, **some_data)}

            @with_fixtures('fix1')
            def test_my_feature(self, fixtures):
                # ...

    """
    def proxy(func):
        func._required_fixtures = names
        return func
    return proxy


class ExpectedFailure(Exception):
    pass


class UnexpectedSuccess(Exception):
    pass


class FuturePlugin(errorclass.ErrorClassPlugin):
    """Hooks our `future` decorator into the nose plugin system"""
    enabled = True
    name = "future"

    future = errorclass.ErrorClass(ExpectedFailure, label='FUTURE', isfailure=False)
    unexpected = errorclass.ErrorClass(UnexpectedSuccess, label='UNEXPECTED',
                                       isfailure=True)


#TODO: write unittests
def future(func):
    """Mark a test as expected to unconditionally fail."""
    @functools.wraps(func)
    def future_decorator(*args, **kw):
        try:
            func(*args, **kw)
        except Exception, ex:
            raise ExpectedFailure("Test failed as expected: %s ... " % str(ex))
        else:
            raise UnexpectedSuccess("Unexpected success for future test")
    return future_decorator
