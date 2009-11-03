#-*- coding: utf-8 -*-
from nose.tools import *
from inyoka.utils.urls import url_for
from inyoka.core.config import config



def test_url_for():
    # set base domain name for correct testing
    config['base_domain_name'] = 'inyoka.local:8080'
    eq_(url_for('portal/index'), '/')
    eq_(url_for('portal/index', _external=True), 'http://inyoka.local:8080/')
    eq_(url_for('portal/index', _anchor='News'), '/#News')
    eq_(url_for('portal/index', _external=True, _anchor='News'), 'http://inyoka.local:8080/#News')
    del config['base_domain_name']
