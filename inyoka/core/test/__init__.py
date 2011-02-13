# -*- coding: utf-8 -*-
"""
    inyoka.core.test
    ~~~~~~~~~~~~~~~~

    This module abstracts nosetest and provides an interface for our unittests
    and doctests.  It also implements various helper classes and functions.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import sys
import unittest
import warnings
from functools import wraps
from urllib2 import urlparse

import nose
from nose.plugins import cover, base, errorclass

from logbook import TestHandler as LogbookTestHandler

from werkzeug import Client
from werkzeug.contrib.testtools import ContentAccessors

from sqlalchemy.util import to_list

from inyoka.context import ctx, _request_ctx_stack
from inyoka.core import database, mail
from inyoka.core.cache import set_cache
from inyoka.core.test import mock
from inyoka.core.test.fixtures import FixtureLoader
from inyoka.core.database import db
from inyoka.core.http import Response
from inyoka.core.resource import IResourceManager
from inyoka.core.exceptions import ImproperlyConfigured
from inyoka.core.templating import template_rendered
from inyoka.utils import flatten_iterator
from inyoka.utils.urls import get_base_url_for_controller


warnings.filterwarnings('ignore', message='lxml does not preserve')
warnings.filterwarnings('ignore', message=r'object\.__init__.*?takes no parameters')

__all__ = ('TestResponse', 'ViewTestCase', 'TestCase', 'with_fixtures',
           'future', 'db', 'Response', 'ctx',
           'DatabaseTestCase', 'TestResourceManager',
           'skip_if_environ', 'todo', 'skip', 'skip_if', 'skip_unless', 'skip_if_database',
           'set_simple_cache')


__all__ = __all__ + tuple(nose.tools.__all__)

dct = globals()
for obj in nose.tools.__all__:
    dct[obj] = getattr(nose.tools, obj)
del dct


_iterables = (list, tuple, set, frozenset)


def flatten_data(data):
    return {d.keys()[0]: list(flatten_iterator(d.values())) for d in data}


class TestResponse(Response, ContentAccessors):
    """Responses for the test client."""


class TestResourceManager(IResourceManager):
    """:class:`~inyoka.core.resource.IResourceManager` implementation to
    manage unittest models.

    Sometimes it's required to implement your own models in unittests
    to ensure your unittests can rely on a not-changing interface.  To register
    those models with the rest of Inyoka you can use the new :class:`IResourceManager`
    interface implemented by :class:`~inyoka.core.test.TestResourceManager`.

    There are two ways to register your models.  The first one is via the
    :attr:`manager` attribute::

        class MyModel(db.Model):
            __tablename__ = '_test_mymodel'

            # resource manager model
            manager = TestResourceManager

            name = db.Column(db.String(200))

    The other way to register your models is via the
    :meth:`TestResourceManager.register_models` method.  This approach is also
    helpful if you do not have a model but a table to register::

        my_table = db.Table('__test_mytable', db.metadata,
            db.Column('id', db.Integer, primary_key=True),
            db.Column('name', db.String(200))
        )
        TestResourceManager.register_models(my_table)

    """

    models = []

    @classmethod
    def register_models(cls, models):
        if not isinstance(models, (list, tuple, set, frozenset)):
            models = [models]
        cls.models.extend(models)


class InyokaTestClient(Client):
    """Works like a regular Werkzeug test client but has some
    knowledge about how Inyoka works to defer the cleanup of the
    request context stack to the end of a with body when used
    in a with statement.
    """

    preserve_context = context_preserved = False

    def open(self, *args, **kwargs):
        if self.context_preserved:
            _request_ctx_stack.pop()
            self.context_preserved = False
        kwargs.setdefault('environ_overrides', {})
        kwargs['inyoka._preserve_context'] = self.preserve_context
        old = _request_ctx_stack.top
        try:
            return Client.open(self, *args, **kwargs)
        finally:
            self.context_preserved = _request_ctx_stack.top is not old

    def __enter__(self):
        self.preserve_context = True
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.preserve_context = False
        if self.context_preserved:
            _request_ctx_stack.pop()


class TestCase(unittest.TestCase):
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
            result.addError(self, sys.exc_info())
            return
        super(TestCase, self).__call__(result)
        try:
            self._post_teardown()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            result.addError(self, sys.exc_info())
            return


class DatabaseTestCase(TestCase):
    """This class provides fixture support."""

    data = {}
    fixtures = []
    custom_cleanup_factories = []
    _loaded_fixtures = []

    def _pre_setup(self):
        super(DatabaseTestCase, self)._pre_setup()

        if self.fixtures:
            loader = FixtureLoader()
            self._loaded_fixtures = data = loader.from_list(self.fixtures)
            self.data = flatten_data(data)

    def _post_teardown(self):
        super(DatabaseTestCase, self)._post_teardown()

        # This is a bit slow because we commit after every DELETE
        # statement.  But to preserve the order of fixtures there's
        # no other way to not break cascade statements and other
        # relationships.
        for factory in self.custom_cleanup_factories:
            for item in factory():
                db.session.delete(item)
                db.session.commit()

        for group in reversed(self._loaded_fixtures):
            for name, objects in group.iteritems():
                for object in objects:
                    db.session.delete(object)
                    db.session.commit()

        # revert all mock objects to get clear passage on the next test
        mock.restore()
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

    def _add_template(self, sender, template=None, context=None):
        self.templates.append((template, context))

    def _pre_setup(self):
        """Setup the test client and url and base domain values"""
        super(ViewTestCase, self)._pre_setup()

        self.client = InyokaTestClient(ctx.dispatcher, TestResponse, use_cookies=True)
        self.base_domain = ctx.cfg['base_domain_name']
        self.base_url = get_base_url_for_controller(self.controller or 'test')
        self.templates = []
        template_rendered.connect(self._add_template)

    def _post_teardown(self):
        super(ViewTestCase, self)._post_teardown()
        template_rendered.disconnect(self._add_template)

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

        Can be used as a context manager.
        """
        kwargs['base_url'] = self.base_url
        return ctx.dispatcher.test_request_context(*args, **kwargs)

    # Advanced Unittest methods for easy unittests

    def assertRedirects(self, response, location):
        assert response.status_code in (301, 302), \
               "Status Code not in (301, 302) got %s" % response.status_code
        assert response.location == urlparse.urljoin(self.base_url, location), \
               "Location did not match, got %s instead" % response.location

    def assertStatus(self, response, status_code):
        nose.tools.eq_(response.status_code, status_code)

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

    def get_context_variable(self, name):
        """Returns a variable from the context passed to the template.

        Raises a ContextVariableDoesNotExist exception if does
        not exist in context.

        :versionadded: 0.2
        :param name: name of variable
        """
        for template, context in self.templates:
            if name in context:
                return context[name]
        raise KeyError(u'Context variable %s does not exist' % name)

    def assertContext(self, name, value):
        """
        Checks if given name exists in the template context
        and equals the given value.

        :versionadded: 0.2
        :param name: name of context variable
        :param value: value to check against
        """

        try:
            self.assertEqual(self.get_context_variable(name), value)
        except KeyError:
            raise AssertionError(u'Expected context:\n%r\n\nActual Variables:\n%r'
                                 % (value, u', '.join(x[1] for x in self.templates)))

    def assertTemplateUsed(self, name):
        """Checks if a given template is used in the request.

        :param name: template name
        """
        for template, context in self.templates:
            if template.name == name:
                return True
        raise AssertionError(u'Template %s not used.  Used templates: %s'
                             % (name, u', '.join(x[0].name for x in self.templates)))


class InyokaPlugin(cover.Coverage):
    """Nose plugin extension

    This plugin prevents modules from being loaded without a configured
    Inyoka environment.

    It also implements our fixture system and fixes the coverage html output.
    Next to this it set's the internal `testing` config value to `True` so that
    our unittest helpers get enabled.

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
        ctx.cfg['testing'] = True
        ctx.load_packages(['tests.*'])

        # Special celery handling.
        #
        # We disable the email sending feature of celery for safety.
        ctx.cfg['celery.send_task_error_emails'] = False

    def options(self, parser, env):
        # Don't setup coverage options,
        # base.Plugin takes care of with-inyoka
        base.Plugin.options(self, parser, env)

    def begin(self):
        """We overwrite this method to push in our database
        setup and to not setup coverage again, since we start it
        quite a lot earlier.
        """
        self._connection = conn = db.get_engine().connect()

        # drop all tables
        db.metadata.drop_all(conn)

        # then we create everything
        database.init_db(bind=conn, is_test=True)

        # clear email outbox
        mail.outbox = []

        _internal_modules_to_skip = ('inyoka.core.tasks',)
        self.skipModules = [i for i in sys.modules.keys() if not i.startswith('inyoka')
                            or i in _internal_modules_to_skip]

    def beforeTest(self, test):
        self._transaction = self._connection.begin()
        db.session.bind = self._connection

    def afterTest(self, test):
        self._transaction.rollback()
        db.session.rollback()
        db.session.remove()

    def finalize(self, result):
        """Cleanup some stuff."""
        # clear email backend outbox.
        mail.outbox = []

        # drop all database tables to leave an empty environment
        db.metadata.drop_all(self._connection)

        # finally close the database connection.
        self._connection.close()

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
        from coverage.config import CoverageConfig
        coverage.stop()
        modules = [module for name, module in sys.modules.items()
                   if self.wantModuleCoverage(name, module)]
        html_reporter = coverage.html.HtmlReporter(coverage._the_coverage)
        config = CoverageConfig()
        config.html_dir = self.coverHtmlDir
        if self.coverHtmlDir:
            if not os.path.exists(self.coverHtmlDir):
                os.makedirs(self.coverHtmlDir)
            html_reporter.report(modules, config)


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
    This may lead into performance issues.
    """
    def decorator(func):
        @wraps(func)
        def _proxy(*args, **kwargs):
            if callable(fixtures):
                # the function defines it's own fixture loader.
                data = fixtures()
            else:
                data = flatten_data(FixtureLoader().from_list(fixtures))
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

def set_simple_cache(func):
    """Set the cache system to 'simple'.

    This also adds the proper configured cache object as the first argument.
    Example::

        @set_simple_cache
        def test_something_furious(cache):
            assert cache.get('some_key_never_exists') is None

    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        _configured_cache = ctx.cfg['caching.system']
        ctx.cfg['caching.system'] = 'simple'
        cache = set_cache()
        func(cache, *args, **kwargs)
        ctx.cfg['caching.system'] = _configured_cache
        cache = set_cache()
    return wrapper


def future(func):
    """Mark a test as expected to unconditionally fail."""
    @wraps(func)
    def future_decorator(*args, **kw):
        try:
            func(*args, **kw)
        except Exception as exc:
            raise ExpectedFailure("Test failed as expected: %s ... " % str(exc))
        else:
            raise UnexpectedSuccess("Unexpected success for future test")
    return future_decorator


def skip_if_environ(name):
    def _wrap_test(fun):
        @wraps(fun)
        def _skips_if_environ(*args, **kwargs):
            if os.environ.get(name):
                raise nose.SkipTest("%s: %s set\n" % (
                    fun.__name__, name))
            return fun(*args, **kwargs)
        return _skips_if_environ
    return _wrap_test


def _skip_test(reason, sign=None):
    def _wrap_test(fun):
        @wraps(fun)
        def _skipped_test(*args, **kwargs):
            raise nose.SkipTest("%s%s" % (sign + ':' if sign else '', reason))
        return _skipped_test
    return _wrap_test


def todo(reason):
    """TODO test decorator."""
    return _skip_test(reason, "TODO")


def skip(reason):
    """Skip test decorator."""
    return _skip_test(reason)


def skip_if(predicate, reason):
    """Skip test if predicate is ``True``."""
    def _inner(fun):
        return predicate and skip(reason)(fun) or fun
    return _inner


def skip_unless(predicate, reason):
    """Skip test if predicate is ``False``."""
    return skip_if(not predicate, reason)


def skip_if_database(name, reason):
    databases = to_list(name)
    return skip_if(database.get_engine().url.drivername in databases, reason)
