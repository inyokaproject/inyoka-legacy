#-*- coding: utf-8 -*-
from nose.tools import *
from werkzeug import EnvironBuilder
from inyoka.core.api import Request, href
from inyoka.core.test import ViewTestCase
from inyoka.paste.controllers import PasteController


class PasteTester(ViewTestCase):

    controller = PasteController

    def test_index(self):
        context = self.get_context('/')
        eq_(context['recent_pastes'], [])

        data = {
            'code': "#!/usr/bin/env python\nprint 'hello world'",
            'language': 'python',
            # 'csrf-token missing'
        }

        response = self.submit_form('/', data=data)
        eq_(response.headers['Location'], href('paste/view_paste', id=1))
        #TODO: add _external=True

        context = self.get_context('/')
        eq_(len(context['recent_pastes']), 1)
        eq_(context['recent_pastes'][0].code, data['code'])
