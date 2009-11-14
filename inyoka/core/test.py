#-*- coding: utf-8 -*-
"""
    inyoka.core.test
    ~~~~~~~~~~~~~~~~

    This module abstracts nosetest and provides an interface for our unittests
    and doctests.  It also implements various helper classes and functions.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import unittest
import warnings

import nose
import nose.plugins

from werkzeug import Client, cached_property
from werkzeug.contrib.testtools import ContentAccessors

from inyoka.core import database
from inyoka.core.database import db
from inyoka.core.context import local, current_application
from inyoka.core.config import config
from inyoka.core.http import Response
from inyoka.core.templating import TEMPLATE_CONTEXT
from inyoka.utils import patch_wrapper
from inyoka.utils.logger import logger
from inyoka.utils.urls import make_full_domain

# disable the logger
logger.disabled = True

warnings.filterwarnings('ignore', message='lxml does not preserve')
warnings.filterwarnings('ignore', message=r'object\.__init__.*?takes no parameters')


class TestResponse(Response, ContentAccessors):
    """Responses for the test client."""


class ViewTestCase(unittest.TestSuite):

    controller = None

    def setUp(self):
        self._client = Client(current_application, response_wrapper=TestResponse)
        self.base_domain = config['base_domain_name']
        subdomain = config['routing.%s.subdomain' % self.controller.name]
        submount = config['routing.%s.submount' %
                           self.controller.name].strip('/')
        self.base_url = make_full_domain(subdomain)

    def get_context(self, path, method='GET', **kwargs):
        ret = self.open(path, method=method, **kwargs)
        return TEMPLATE_CONTEXT

    def open(self, path, *args, **kw):
        if not 'follow_redirects' in kw:
            kw['follow_redirects'] = True
        if not path.endswith('/'):
            path += '/'
        kw['base_url'] = self.base_url
        kw['buffered'] = True
        response = self._client.open(path, *args, **kw)

        # do we need to put the application on a local at all?
        # inyoka.application.application should always exist…
        from inyoka.application import application
        local.application = application

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


class InyokaPlugin(nose.plugins.Plugin):
    """Nose plugin extension

    This prevents modules from being loaded without a configured Inyoka
    environment.

    """
    enabled = False
    enableOpt = 'inyoka_config'
    name = 'inyoka'
    _started = False

    def add_options(self, parser, env=os.environ):
        """Add command-line options for this plugin"""
        env_opt = 'NOSE_WITH_%s' % self.name.upper()
        env_opt.replace('-', '_')

        parser.add_option("--with-%s" % self.name,
                          dest=self.enableOpt, type="string",
                          default="",
                          help="Setup Inyoka environment with the config file"
                          " specified by ATTR [NOSE_ATTR]")

    def configure(self, options, conf):
        """Configure the plugin"""
        self.config_file = None
        self.conf = conf
        if hasattr(options, self.enableOpt):
            self.enabled = bool(getattr(options, self.enableOpt))
            self.config_file = getattr(options, self.enableOpt)

    def startTest(self, test):
        """Called before each test seperately to support our
        own fixture system.
        """
        t = test.test
        if hasattr(t, 'test') and hasattr(t.test, '_required_fixtures'):
            self._started = True
            # reset the database data.  That way we can assure
            # that we get a clear database
            database.metadata.drop_all()
            database.init_db()
            for fixture in t.test._required_fixtures:
                try:
                    functions = test.context.fixtures[fixture]
                    instances = [func() for func in functions]
                    db.session.add_all(instances)
                    db.session.commit()
                except:
                    db.session.rollback()

    def stopTest(self, test):
        if self._started:
            # we clear our database, just to be sure we leave
            # a clean context
            database.metadata.drop_all()
            database.init_db()
            self._started = False

    def wantClass(self, cls):
        # we want view test cases to be loaded with no matter
        # if they are
        if issubclass(cls, ViewTestCase):
            return True
        else:
            return None


#TODO: add json support
#TODO: write unittests
def fixture(model, **kwargs):
    """Insert some test fixtures into the database"""
    def onload():
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
def future(fn):
    """Mark a test as expected to unconditionally fail."""
    fn_name = fn.func_name
    def decorated(*args, **kw):
        try:
            fn(*args, **kw)
        except Exception, ex:
            print ("Future test '%s' failed as expected: %s " % (
                fn_name, str(ex)))
            return True
        else:
            raise AssertionError(
                "Unexpected success for future test '%s'" % fn.func_name)
    return patch_wrapper(decorated, fn)


def run_suite(module='inyoka'):
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
