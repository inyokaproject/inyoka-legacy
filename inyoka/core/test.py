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
from inyoka.core.templating import TemplateResponse
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

    controller = None
    response = None
    client = Client(current_application, response_wrapper=ResponseWrapper)

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.url_map = Map(self.controller.url_rules)
        self.subdomain = config['routing.%s.subdomain' % self.controller.name]
        self.submount = config['routing.%s.submount' %
                               self.controller.name].strip('/')

    def open_location(self, path, method='GET', **kwargs):
        """Open a location (path)"""
        if not 'follow_redirects' in kwargs:
            kwargs['follow_redirects'] = True
        if not path.endswith('/'):
            path += '/'

        path = self.submount + path
        base_url = make_full_domain(self.subdomain)
        self.response = self.client.open(path, method=method,
            base_url=base_url, **kwargs)

        return self.response

    def get_context(self, path, method='GET', **kwargs):
        """This method returns the internal context of the templates
        so that we can check it in our view-tests."""
        response = self.open_location(path, method, **kwargs)

        # we assume to test a @templated view function.  We don't have that
        # much view functions where we don't use the @ templated decorator
        # or even a `TemplateResponse` as return type.
        # print response.app, response.headers, response.status
        assert isinstance(response.app, TemplateResponse)
        return response.app.template_context

    def login(self, credentials):
        return

    def logout(self):
        return



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
