#-*- coding: utf-8 -*-
from nose.tools import *
from werkzeug import EnvironBuilder
from inyoka.core.api import Request, href
from inyoka.core.test import ViewTestCase, fixture, with_fixtures
from inyoka.core.models import User
from inyoka.paste.controllers import PasteController
from inyoka.paste.models import Entry


#TODO: this fixture thingy here is mostly for test reasons.
#      Move it into it's own test suite!
DATA = {
    'code': u"#!/usr/bin/env python\nprint 'hello world'",
    'language': 'python',
    'author': User.query.first()
}


class PasteTester(ViewTestCase):

    controller = PasteController

    fixtures = {
        'pastes': [
            fixture(Entry, **DATA)
    ]}

    @with_fixtures('pastes')
    def test_index(self):
        #TODO: for now this mostly just tests the fixture
        #      feature, so add real tests!
        context = self.get_context('/')
        eq_(len(context['recent_pastes']), 1)
        eq_(context['recent_pastes'][0].code, DATA['code'])

    def test_new_paste(self):
        response = self.submit_form('/', data=DATA)
        eq_(response.headers['Location'], href('paste/view', id=1))
        context = self.get_context('/')
        eq_(len(context['recent_pastes']), 1)
