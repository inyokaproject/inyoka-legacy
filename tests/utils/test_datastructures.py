# -*- coding: utf-8 -*-
"""
    test_datastructures

    Unittests for inyoka used datastructures.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.utils.datastructures import BidiMap


def test_bidimap():
    map = BidiMap({
        1: 'dump',
        2: 'smartly',
        3: 'clever'
    })
    eq_(map[1], 'dump')
    eq_(map[2], 'smartly')
    eq_(map[3], 'clever')
    # and reversed
    eq_(map['dump'], 1)
    eq_(map['smartly'], 2)
    eq_(map['clever'], 3)


@raises(ValueError)
def test_bidimap_unique():
    map = BidiMap({
        1: 'maxorious',
        2: 'enteorious',
        3: 'barorious',
        4: 'barorious'
    })
