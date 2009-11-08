#-*- coding: utf-8 -*-
from nose.tools import *
from inyoka.utils.urls import url_for
from inyoka.core.config import config



def test_url_for():
    # set base domain name for correct testing
    domain = config['base_domain_name']
    eq_(url_for('portal/index'), '/')
    eq_(url_for('portal/index', _external=True), 'http://%s/' % domain)
    eq_(url_for('portal/index', _anchor='News'), '/#News')
    eq_(url_for('portal/index', _external=True, _anchor='News'), 'http://%s/#News' % domain)
