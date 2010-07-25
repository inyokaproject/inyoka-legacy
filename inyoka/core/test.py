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
import unittest2
import warnings
import traceback
from functools import partial, wraps
from pprint import pformat

import nose
from nose.plugins import cover, base, errorclass

from werkzeug import Client, create_environ
from werkzeug.contrib.testtools import ContentAccessors
from minimock import mock, Mock, TraceTracker, restore as revert_mocks

from inyoka.l10n import parse_timestamp, parse_timeonly
from inyoka.context import ctx
from inyoka.core import database
from inyoka.core.database import db
from inyoka.core.http import Response, Request, get_bound_request
from inyoka.utils.logger import logger
from inyoka.utils.urls import make_full_domain, get_host_port_mapping, \
    get_base_url_for_controller


logger.disabled = True

warnings.filterwarnings('ignore', message='lxml does not preserve')
warnings.filterwarnings('ignore', message=r'object\.__init__.*?takes no parameters')

__all__ = ('TestResponse', 'ViewTestCase', 'TestCase', 'with_fixtures',
           'future', 'tracker', 'mock', 'Mock', 'revert_mocks', 'db', 'Response',
           'ctx', 'FixtureLoader', 'DatabaseTestCase', 'refresh_database')
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


# Fixture Framework
#
# The code is based on `bootalchemy <http://pypi.python.org/pypi/bootalchemy>`
# but was heavily modified to better fit Inyokas database system management.
#


class FixtureLoader(object):
    """This class is responsible of loading fixtures."""

    default_encoding = 'utf-8'

    def cast(type_, cast_func, value):
        if type(value) == type_:
            return value
        else:
            return cast_func(value)

    default_casts = {
        db.Integer:int,
        db.Unicode: partial(cast, unicode, lambda x: unicode(x, default_encoding)),
        db.Date: parse_timestamp,
        db.DateTime: parse_timestamp,
        db.Time: parse_timeonly,
        db.Float:float,
        db.Boolean: partial(cast, bool, lambda x: x.lower() not in ('f', 'false', 'no', 'n')),
        db.Binary: partial(cast, str, lambda x: x.encode('base64')),
        db.PGArray: list
    }

    def __init__(self, references=None, check_types=True):
        if references is None:
            self._references = {}
        else:
            self._references = references

        self.check_types = check_types

    def clear(self):
        """Clear the existing references."""
        self._references = {}

    def create_obj(self, cls, item):
        """Create an object with the given data"""
        return cls(**item)

    def resolve_value(self, value):
        """Resolve `value`.

        This method resolves references on columns or even whole
        objects as well as nested references.
        """
        if isinstance(value, basestring):
            if value.startswith('&'):
                return None
            elif value.startswith('*'):
                if value[1:] in self._references:
                    return self._references[value[1:]]
                else:
                    raise Exception('The pointer {val} could not be found. '
                                    'Make sure that {val} declared before '
                                    'it is used.'.format(val=value))
        elif isinstance(value, dict):
            keys = value.keys()
            if len(keys) == 1 and keys[0].startswith('!'):
                cls_name = keys[0][1:]
                items = value[keys[0]]
                cls = self.get_cls(cls_name)

                if isinstance(items, dict):
                    return self.add_cls_with_values(cls, items)
                elif isinstance(items, (list, set)):
                    return self.add_clses(cls, items)
                else:
                    raise TypeError('You can only give a nested value a list or a dict. '
                                    'You tried to feed a %s into a %s.'
                                    % (items.__class__.__name__, cls_name))
        elif isinstance(value, (list, set)):
            return type(value)([self.resolve_value(list_item) for list_item in value])

        return value

    def has_references(self, item):
        """Check if `item` has references of any kind"""
        for key, value in item.iteritems():
            if isinstance(value, basestring) and value.startswith('&'):
                return True

    def add_reference(self, key, obj):
        """Add a reference to the internal reference dictionary"""
        self._references[key[1:]] = obj

    def set_references(self, obj, item):
        """Extracts and stores the value of an object in the reference counter."""
        for key, value in item.iteritems():
            if isinstance(value, basestring) and value.startswith('&'):
                self._references[value[1:]] = getattr(obj, key)
            if isinstance(value, (list, set)):
                for i in value:
                    if isinstance(value, basestring) and i.startswith('&'):
                        self._references[value[1:]] = getattr(obj, value[1:])

    def _check_types(self, cls, obj):
        """Validate all types and cast them to better matching types if possible."""
        if not self.check_types:
            return obj
        mapper = db.class_mapper(cls)
        for table in mapper.tables:
            for key in obj.keys():
                col = table.columns.get(key, None)
                value = obj[key]
                if value is not None and col is not None and col.type is not None:
                    for type_, func in self.default_casts.iteritems():
                        if isinstance(col.type, type_):
                            obj[key] = func(value)
                            break
                if value is None and col is not None and isinstance(col.type, (db.String, db.Unicode)):
                    obj[key] = ''
        return obj

    def get_cls(self, name):
        """Try to find the right class for `name`"""
        cls = None
        models = list(db.ISchemaController.get_models())
        names = [m.__name__ for m in models]
        if name in names:
            cls = models[names.index(name)]

        # check that the class was found.
        if cls is None:
            raise AttributeError('Model %s not found' % name)

        return cls

    def add_cls_with_values(self, cls, values):
        """Return a new objects with resolved `values`.

        :param cls: A type to initiate.
        :param values: A dictionary with values for initialisation.
        """
        ref_name = None
        keys = values.keys()
        if len(keys) == 1 and keys[0].startswith('&') and isinstance(values[keys[0]], dict):
            ref_name = keys[0]
            values = values[ref_name] # ie. item.values[0]

        # Values is a dict of attributes and their values for any ObjectName.
        # Copy the given dict, iterate all key-values and process those with
        # special directions (nested creations or links).
        resolved_values = values.copy()
        for key, value in resolved_values.iteritems():
            resolved_values[key] = self.resolve_value(value)

        # _check_types currently does nothing (unless you call the loaded with a check_types parameter)
        resolved_values = self._check_types(cls, resolved_values)

        obj = self.create_obj(cls, resolved_values)
        self.session.add(obj)

        if ref_name:
            self.add_reference(ref_name, obj)
        if self.has_references(values):
            self.session.flush()
            self.set_references(obj, values)

        return obj

    def add_clses(self, cls, items):
        """Returns a list of the new objects.
        These objects are already in session, so you don't
        *need* to do anything with them.

        """
        objects = []
        for item in items:
            obj = self.add_cls_with_values(cls, item)
            objects.append(obj)
        return objects

    def from_list(self, session, data):
        """Initialize `data` in `session`.  See unittest docs for more details."""
        self.session = session
        cls = None
        item = None
        group = None
        skip_keys = ['nocommit']
        new_data = {}
        try:
            for group in data:
                for cls, items in group.iteritems():
                    if cls in skip_keys:
                        continue
                    if isinstance(cls, basestring) and cls not in skip_keys:
                        cls = self.get_cls(cls)
                    new_data[cls.__name__] = self.add_clses(cls, items)
                if 'nocommit' not in group:
                    session.commit()
        except Exception:
            self.log_error(sys.exc_info()[2], data, cls, item)
            db.session.rollback()
            raise

        self.session = None
        return new_data

    def log_error(self, e, data, cls, item):
        msg = 'error occured while loading fixture data with output:\n%s' % pformat(data)
        msg += '\nclass: %s' % cls
        msg += '\nitem: %s' % item
        msg += '\n%s' % traceback.format_exc(e)
        logger.error(msg)


class TestCase(unittest2.TestCase):
    """TestCase for the Inyoka test framework.

    A TestCase holds various test methods for unittesting and
    is able to use our own fixtures framework.
    """

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

    def __call__(self, result=None):
        """
        Wrapper around default __call__ method to perform common test
        set up. This means that user-defined Test Cases aren't required to
        include a call to super().setUp().
        """
        try:
            self._pre_setup()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            import sys
            result.addError(self, sys.exc_info())
            return
        super(TestCase, self).__call__(result)
        try:
            self._post_teardown()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            import sys
            result.addError(self, sys.exc_info())
            return


class DatabaseTestCase(TestCase):
    """This class provides fixture support."""

    _started = False
    data = {}
    fixtures = {}
    custom_cleanup_factories = []

    def _pre_setup(self):
        super(DatabaseTestCase, self)._pre_setup()

        if self.fixtures:
            loader = FixtureLoader()
            self.data = loader.from_list(db.session, self.fixtures)

    def _post_teardown(self):
        super(DatabaseTestCase, self)._post_teardown()

        for group in self.data:
            try:
                for cls in self.data[group]:
                    db.session.delete(cls)
            except TypeError:
                db.session.delete(self.data[group])

        for factory in self.custom_cleanup_factories:
            for item in factory():
                db.session.delete(item)

        db.session.commit()

        # revert all mock objects to get clear passage on the next test
        revert_mocks()
        try:
            db.session.close()
        except db.SQLAlchemyError:
            db.session.rollback()
            raise

        for callback in ctx.dispatcher.cleanup_callbacks:
            callback()


class ViewTestCase(DatabaseTestCase):
    """A test case suitable to test view methods properly"""

    controller = None

    def _pre_setup(self):
        """Setup the test client and url and base domain values"""
        super(ViewTestCase, self)._pre_setup()

        self.client = Client(ctx.dispatcher, response_wrapper=TestResponse,
                             use_cookies=True)
        self.base_domain = ctx.cfg['base_domain_name']
        self.base_url = get_base_url_for_controller(self.controller or 'test')

    def get_context(self, path, method='GET', **kwargs):
        """
        Return the template context from a view wrapped by :func:`templated`.
        """
        response = self.open(path, method=method, **kwargs)
        try:
            return response._template_context
        except AttributeError:
            raise ImproperlyConfigured(u'You must set inyoka.debug to \'True\'')

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
        """Submit a form to `path` with `data`.

        This method takes care of CSRF token handling.

        :param path: The path to query.
        :param data: A dictionary containing the form data.
        :param follow_redirects: Follow redirects.
        """
        response = self.get(path)
        try:
            form = response.lxml.xpath('//form')[0]
        except IndexError:
            raise AssertionError('no form on page')
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
        assert response.status_code in (301, 302), \
               "Status Code not in (301, 302) got %s" % response.status_code
        assert response.location == os.path.join(self.base_url, location), \
               "Location did not match, got %s instead" % response.location

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


class InyokaPlugin(cover.Coverage):
    """Nose plugin extension

    This plugin prevents modules from being loaded without a configured
    Inyoka environment.

    It also implements our fixture system and fixes the coverage html output.

    """

    enabled = False
    enableOpt = 'inyoka_config'
    name = 'inyoka'

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
        database.init_db(bind=engine, is_test=True)

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

    def wantClass(self, cls):
        """Check if we can use a `cls` for unittest purposes.  This adds
        `ViewTestCase` to the list of possible unittest interfaces."""
        if issubclass(cls, (DatabaseTestCase, ViewTestCase)) and cls is not ViewTestCase:
            return True
        elif cls is ViewTestCase:
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


def refresh_database(func):
    """Refresh the database right after the decorated function was called"""
    @wraps(func)
    def decorator(*args, **kwargs):
        ret = func(*args, **kwargs)
        # drop all data afterwards and initialize the database again.
        database.metadata.drop_all(bind=database.get_engine())
        database.init_db(bind=database.get_engine(), is_test=True)
        return ret
    return decorator


def with_fixtures(fixtures):
    """Mark this function to work with some fixture.

    Example usage:

    .. code-block:: python

        fixtures = [{'User': {'username': 'Paul', 'email': 'paul@example.com'}}]

        @with_fixtures(fixtures)
        def test_my_feature(fixtures):
            # your tests here
            pass

    Note that the database is refreshed right after function execution.
    This may lead into perforamnce issues.
    """
    def decorator(func):
        @refresh_database
        @wraps(func)
        def _proxy(*args, **kwargs):
            if callable(fixtures):
                # the function defines it's own fixture loader.
                data = fixtures()
            else:
                data = FixtureLoader().from_list(db.session, fixtures)
            return func(data, *args, **kwargs)
        return _proxy
    return decorator


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
    @wraps(func)
    def future_decorator(*args, **kw):
        try:
            func(*args, **kw)
        except Exception as ex:
            raise ExpectedFailure("Test failed as expected: %s ... " % str(ex))
        else:
            raise UnexpectedSuccess("Unexpected success for future test")
    return future_decorator
