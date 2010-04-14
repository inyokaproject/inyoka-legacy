# -*- coding: utf-8 -*-
"""
    test_routing
    ~~~~~~~~~~~~

    Unittests for the inyoka routing utilities.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GN UGPL, see LICENSE for more details.
"""
from datetime import date
from werkzeug.routing import ValidationError
from inyoka.core.test import *
from inyoka.core.routing import DateConverter



def test_date_converter():
    map = None
    d = DateConverter(map)
    eq_(d.regex, r'\d{4}\/\d\d\/\d\d')
    eq_(d.to_python('2009/09/05'), date(2009, 9, 5))
    d = DateConverter(map, '%Y-%m-%d')
    eq_(d.regex, r'\d{4}\-\d\d\-\d\d')
    eq_(d.to_python('2009-09-05'), date(2009, 9, 5))
    eq_(d.to_url(date(2009, 9, 5)), '2009-09-05')
    d = DateConverter(map, '%Y%%%m%%%d')
    eq_(d.to_python('2009%09%05'), date(2009, 9, 5))
    eq_(d.to_url(date(2009, 9, 5)), '2009%2509%2505')
    d = DateConverter(map, '\n %Y \\foo %m foo %% bar %d')
    eq_(d.to_python('\n 2009 \\foo 05 foo % bar 03'),
        date(2009, 5, 3))
    eq_(d.to_url(date(2009,5,3)),
        '%0A%202009%20%5Cfoo%2005%20foo%20%25%20bar%2003')
    assert_raises(ValidationError, DateConverter, map, '%Y %M')
    d = DateConverter(map, '%Y %Y')
    assert_raises(ValidationError, d.to_python, '2009 2009')
    d = DateConverter(map, '%Y %m')
    assert_raises(ValidationError, d.to_python, '2009 13')
