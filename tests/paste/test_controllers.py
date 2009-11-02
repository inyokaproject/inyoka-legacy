from nose.tools import *
from werkzeug import EnvironBuilder
from inyoka.core.api import Request, href
from inyoka.core.test import ViewTester
from inyoka.paste.controllers import PasteController

view = ViewTester(PasteController)

def test_index():

    resp, tctx = view('/')
    eq_(tctx['recent_pastes'], [])

    data = {
        'code': "#!/usr/bin/env python\nprint 'hello world'",
        'language': 'python',
    }
    resp, tctx = view('/', data=data, method='POST')
    print `resp.headers`
    print `resp.data`
    eq_(resp.headers['Location'], href('paste/view_paste', id=1))

    resp, tctx = view('/')
    eq_(len(tctx['recent_pastes']), 1)
    eq_(tctx['recent_pastes'][0].code, data['code'])


