# -*- coding: utf-8 -*-
"""
    test_diff3
    ~~~~~~~~~~

    Unittests for the inyoka utilities.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.utils.diff3 import merge, DiffConflict


def test_merge():
    in1 = """AAA 001
AAA 002
AAA 003
AAA 004
AAA 005
AAA 006
AAA 007
AAA 008
AAA 009
AAA 010
AAA 011
AAA 012
AAA 013
AAA 014
"""

    in2 = """AAA 001
AAA 002
AAA 005
AAA 006
AAA 007
AAA 008
BBB 001
BBB 002
AAA 009
AAA 010
BBB 003
"""

    in3 = """AAA 001
AAA 002
AAA 003
AAA 004
AAA 005
AAA 006
AAA 007
AAA 008
CCC 001
CCC 002
CCC 003
AAA 012
AAA 013
AAA 014
"""
    result = merge(in1, in2, in3)

    expected = """AAA 001
AAA 002
AAA 005
AAA 006
AAA 007
AAA 008
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
BBB 001
BBB 002
AAA 009
AAA 010
BBB 003
========================================
CCC 001
CCC 002
CCC 003
AAA 012
AAA 013
AAA 014
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"""
    eq_(result, expected)


def test_raises_diffconflict_first_line():
    in1 = '''
AAA 001
AAA 002
AAA 003
AAA 004'''

    in2 = '''
AAA 002
AAA 002
AAA 003
BBB 001'''

    in3 = '''
AAA 003
AAA 002
AAA 003
BBB 002'''

    assert_raises(DiffConflict, merge, in1, in2, in3, False)


def test_raises_diffconflict_fourth_line():
    in1 = '''
AAA 001
AAA 002
AAA 003
AAA 004'''

    in2 = '''
AAA 001
AAA 002
AAA 003
BBB 001'''

    in3 = '''
AAA 001
AAA 002
AAA 003
BBB 002'''

    assert_raises(DiffConflict, merge, in1, in2, in3, False)


def test_successfull_merge():
    in1 = '''
AAA 001
AAA 002
AAA 003
AAA 004'''

    in2 = '''
AAA 001
AAA 002
AAA 003
AAA 004'''

    in3 = '''
AAA 001
AAA 002
AAA 003
AAA 005'''

    expected = '''
AAA 001
AAA 002
AAA 003
AAA 005'''

    eq_(merge(in1, in2, in3), expected)


def test_only_two_changed():
    in1 = 'AAA 001'
    in2 = 'AAA 002'
    in3 = 'AAA 001'
    expected = '''<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
AAA 002
========================================
AAA 001
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'''
    eq_(merge(in1, in2, in3), expected)
