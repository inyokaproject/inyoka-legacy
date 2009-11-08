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
import tempfile
import unittest
import warnings
from os import path

import nose
from lxml import etree
from html5lib import HTMLParser
from html5lib.treebuilders import getTreeBuilder

from werkzeug import Client, cached_property
from inyoka.core import database
from inyoka.core.context import local, get_application
from inyoka.core.config import config
from inyoka.core.http import Request, Response
from inyoka.core.templating import TEMPLATE_CONTEXT
from inyoka.utils.logger import logger
from inyoka.utils.urls import make_full_domain

# disable the logger
logger.disabled = True

warnings.filterwarnings('ignore', message='lxml does not preserve')
warnings.filterwarnings('ignore', message=r'object\.__init__.*?takes no parameters')

html_parser = HTMLParser(tree=getTreeBuilder('lxml'))


class TestResponse(Response):
    """Responses for the test client."""

    @cached_property
    def html(self):
        return html_parser.parse(self.data)


class ViewTestCase(unittest.TestCase):

    controller = None

    def setUp(self):
        from inyoka.application import application
        self._client = Client(application, response_wrapper=TestResponse)
        self.base_domain = config['base_domain_name']
        subdomain = config['routing.%s.subdomain' % self.controller.name]
        submount = config['routing.%s.submount' %
                           self.controller.name].strip('/')
        self.base_url = make_full_domain(subdomain)

    def get_context(self, path, method='GET', **kwargs):
        self.open(path, method=method, **kwargs)
        c = TEMPLATE_CONTEXT
        return c

    def open(self, path, *args, **kw):
        app = get_application()
        if not 'follow_redirects' in kw:
            kw['follow_redirects'] = True
        if not path.endswith('/'):
            path += '/'
        kw['base_url'] = self.base_url
        kw['buffered'] = True
        response = self._client.open(path, *args, **kw)
        local.application = app

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
            form = response.html.xpath('//form')[0]
        except IndexError:
            raise RuntimeError('no form on page')
        csrf_token = form.xpath('//input[@name="_csrf_token"]')[0]
        data['_csrf_token'] = csrf_token.attrib['value']
        action = self.normalize_local_path(form.attrib['action'])
        return self.post(action, method=form.attrib['method'].upper(),
                                data=data, follow_redirects=follow_redirects)


def run_suite():
    import nose.plugins.builtin
    plugins = [x() for x in nose.plugins.builtin.plugins]

    config['debug'] = True
    engine = database.get_engine()
    # first we cleanup the existing database
    database.metadata.drop_all(bind=engine)
    # then we create everything
    database.metadata.create_all(bind=engine)
    try:
        nose.main(plugins=plugins)
    finally:
        # and at the end we clean up our stuff
        database.metadata.drop_all(bind=engine)
