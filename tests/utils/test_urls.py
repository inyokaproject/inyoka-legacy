# -*- coding: utf-8 -*-
from nose.tools import *
from inyoka.core.api import href
from inyoka.core.context import config



def test_href():
    # set base domain name for correct testing
    domain = config['base_domain_name']
    eq_(href('portal/index'), '/')
    eq_(href('portal/index', _external=True), 'http://%s/' % domain)
    eq_(href('portal/index', _anchor='News'), '/#News')
    eq_(href('portal/index', _external=True, _anchor='News'), 'http://%s/#News' % domain)
