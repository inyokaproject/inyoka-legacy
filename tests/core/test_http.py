#-*- coding: utf-8 -*-
from nose.tools import *
from inyoka.core.http import redirect, BadRequest
from inyoka.core.config import config



def test_redirect_external_source():
    config['base_domain_name'] = 'inyoka.local:8080'
    assert_raises(BadRequest, redirect, 'http://ubuntuusers.de')
    del config['base_domain_name']
