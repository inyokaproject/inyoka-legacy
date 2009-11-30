# -*- coding: utf-8 -*-
from nose.tools import *
from inyoka.core.api import href
from inyoka.core.test import ViewTestCase, fixture, with_fixtures
from inyoka.core.auth.models import User
from inyoka.paste.controllers import PasteController
from inyoka.paste.models import Entry


def get_data():
    author = User.query.first()
    return {
        'code': u"print 'hello world'",
        'language': 'python',
        'author': author
    }


class PasteTester(ViewTestCase):

    controller = PasteController

    fixtures = {
        'pastes': [
            fixture(Entry, get_data)
    ]}

    @with_fixtures('pastes')
    def test_index(self):
        #TODO: for now this mostly just tests the fixture
        #      feature, so add real tests!
        context = self.get_context('/')
        eq_(len(context['recent_pastes']), 1)
        eq_(context['recent_pastes'][0].code, u"print 'hello world'")

    def test_new_paste(self):
        response = self.submit_form('/', data=get_data())
        eq_(response.headers['Location'], href('paste/view', id=1))
        context = self.get_context('/')
        eq_(len(context['recent_pastes']), 1)
