#-*- coding: utf-8 -*-
"""
    inyoka.core.test
    ~~~~~~~~~~~~~~~~

    This module abstracts nosetest and provides an interface for our unittests
    and doctests.  It also implements various helper classes and functions.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
import os
import sys
import urlparse
import shutil
import unittest
import tempfile
import nose
from os import path
from functools import update_wrapper
from nose.plugins.base import Plugin
from werkzeug import Client, BaseResponse, EnvironBuilder
from inyoka.core.config import config
from inyoka.core.context import current_application
from inyoka.core.database import db
from inyoka.core.http import Request
from inyoka.core.routing import href, Map, IController
from inyoka.utils.logger import logger
from inyoka.utils.urls import make_full_domain

# disable the logger
logger.disabled = True


class Context(object):
    """
    This is the context for our tests. It provides
    some required things like the `admin` and `user`
    attributes to create a overall test experience.
    """
    admin = None
    res_dir = None
    anonymous = None
    instance_dir = None

    def setup_instance(self, instance_dir):
        """
        Setup the test context. That means: Create an admin
        and normal test user and patch required libraries.
        """
        self.instance_dir = instance_dir
        #TODO: setup admin, anonymous once models are up again

    def teardown_instance(self):
        db.session.rollback()
        db.session.expunge_all()
        db.metadata.drop_all()
        try:
            os.rmdir(self.instance_dir)
        except:
            # fail silently
            pass


# initialize the test context
context = Context()


class ResponseWrapper(object):

    def __init__(self, app, status, headers):
        self.app = app
        self.status = status
        self.headers = headers


class ViewTestCase(unittest.TestCase):

    component = 'portal'
    response = None
    client = Client(current_application, response_wrapper=ResponseWrapper)

    def open_location(self, path, method='GET', **kwargs):
        """Open a location (path)"""
        if not 'follow_redirects' in kwargs:
            kwargs['follow_redirects'] = True
        self.response = self.client.open(path, method=method,
            base_url=href(self.component), **kwargs)
        return self.response

    def get_context(self, path, method='GET', **kwargs):
        """This method returns the internal context of the templates
        so that we can check it in our view-tests."""
        response = self.open_location(path, method, **kwargs)

        # we assume to test a @templated view function.  We don't have that
        # much view functions where we don't use the @ templated decorator
        # or even a `TemplateResponse` as return type.
        assert isinstance(response.app, TemplateResponse)
        return response.app.template_context

    def login(self, credentials):
        return

    def logout(self):
        return


def viewtest(location=None, method='GET', component='portal', **bkw):
    """
    This decorator is used to create an easy test-environment. Example usage::

        @viewtest('/', component='forum')
        def test_forum_index(client, tctx, ctx):
            assert tctx['is_index'] == True

    As you see this decorator adds the following arguments to the function
    call::

        `resp`
            The returned response. With that we are able to check for
            custom response headers and other things.
        `tctx`
            This is the template context returned by view functions decorated
            with the @templated decorator. So it's required to test a @templated
            function if you use the @view_test decorator.
        `ctx`
            The overall test context. It's a `Context` instance with some methods
            and attributes to ensure a easy test experience.

    :param location: The script path of the view. E.g ``/forum/foobar/``.
                     If not given the `tctx` supplied as an argument
                     of the test-function will be `None`.
    :param method:  The method of the request. It must be one of GET, POST,
                    HEAD, DELETE or PUT.
    :param component: The component of the inyoka portal.
                      E.g portal, forum, paste…
    :param bkw: You can also use the kwargs for all arguments
                :meth:`werkzeug.test.Client.open` uses to supply
                `data` and other things.
    """
    def _wrapper(func):
        def decorator(*args, **kwargs):
            client = Client(application, response_wrapper=ResponseWrapper)
            if not 'follow_redirects' in bkw:
                bkw['follow_redirects'] = True
            if location is not None:
                resp = client.open(location, method=method,
                                   base_url=href(component), **bkw)
                assert isinstance(resp.app, TemplateResponse)
                tctx = resp.app.temmplate_context
            else:
                tctx = None
            args = (resp, tctx, context) + args
            return func(*args, **kwargs)
        return update_wrapper(decorator, func)
    return _wrapper


def setup_folders():
    tmpdir = tempfile.gettempdir()
    instance_folder = os.path.join(tmpdir, 'inyoka_test')
    if not path.exists(instance_folder):
        os.mkdir(instance_folder)
        config['media_root'] = os.path.join(instance_folder, 'media')
        os.mkdir(config['media_root'])

    return instance_folder


#XXX: yet unused
def _initialize_database(uri):
    from sqlalchemy import create_engine
    from migrate.versioning import api
    from migrate.versioning.repository import Repository
    from migrate.versioning.exceptions import DatabaseAlreadyControlledError, \
                                              DatabaseNotControlledError

    repository = Repository('inyoka/migrations')

    try:
        schema = api.ControlledSchema(db.engine, repository)
    except DatabaseNotControlledError:
        pass

    try:
        schema = api.ControlledSchema.create(db.engine, repository, None)
    except DatabaseAlreadyControlledError:
        pass

    api.upgrade(db.engine, repository, None)


def run_suite(tests_path=None, clean_db=False, base=None):
    if tests_path is None:
        raise RuntimeError('You must specify a path for the unittests')
    # setup our folder structure
    instance_dir = setup_folders()
    #XXX: this raises, need to find out why
    #config['debug'] = True

    # initialize the database
    #XXX: _initialize_database(config['database_url'])
    db.metadata.create_all()

    # setup the test context
    _res = path.join(tests_path, 'res')
    if not path.exists(_res):
        os.mkdir(_res)
    context.res_dir = _res
    context.setup_instance(instance_dir)

    import nose.plugins.builtin
    plugins = [x() for x in nose.plugins.builtin.plugins]
    try:
        nose.main(plugins=plugins)
    finally:
        # cleanup the test context
        context.teardown_instance()
        shutil.rmtree(instance_dir)
        if os.path.isdir(config['media_root']):
            shutil.rmtree(config['media_root'])
        del config['media_root']

        # optionally delete our test database
        if clean_db and db.engine.url.drivername == 'sqlite':
            try:
                database = db.engine.url.database
                if path.isabs(db.engine.url.database):
                    os.remove(database)
                else:
                    os.remove(path.join(tests_path, path.pardir, database))
            except (OSError, AttributeError):
                # fail silently
                pass

class ViewTester(object):
    def __init__(self, Controller):
        self.app_name = Controller.name
        self.url_map = Map(Controller.url_rules)
        self.subdomain = config['routing.%s.subdomain' % self.app_name]
        self.submount = config['routing.%s.submount' % self.app_name].strip('/')

    def __call__(self, path, **kwargs):
        e = EnvironBuilder(self.submount + path,
                           'http://%s/' % make_full_domain(self.subdomain),
                           **kwargs)
        environ = e.get_environ()
        request = Request(environ, get_application())

        adapter = self.url_map.bind_to_environ(environ,
                                               make_full_domain(self.subdomain))
        view_name, ctx = adapter.match(self.submount + path)
        view = IController._endpoint_map[self.app_name][view_name]

        response = view(request, **ctx)

        return response, getattr(response, 'template_context', None)
