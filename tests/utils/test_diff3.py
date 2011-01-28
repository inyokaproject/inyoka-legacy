# -*- coding: utf-8 -*-
"""
    test_diff3
    ~~~~~~~~~~

    Unittests for the inyoka utilities.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.utils.diff3 import merge, DiffConflict, generate_udiff, \
    DiffRenderer, prepare_udiff


def test_merge():
    old = """AAA 001
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

    other = """AAA 001
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

    new = """AAA 001
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
    result = merge(old, other, new)

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
    old = '''
AAA 001
AAA 002
AAA 003
AAA 004'''

    other = '''
AAA 002
AAA 002
AAA 003
BBB 001'''

    new = '''
AAA 003
AAA 002
AAA 003
BBB 002'''

    assert_raises(DiffConflict, merge, old, other, new, False)


def test_raises_diffconflict_fourth_line():
    old = '''
AAA 001
AAA 002
AAA 003
AAA 004'''

    other = '''
AAA 001
AAA 002
AAA 003
BBB 001'''

    new = '''
AAA 001
AAA 002
AAA 003
BBB 002'''

    assert_raises(DiffConflict, merge, old, other, new, False)


def test_successful_merge():
    old = '''
AAA 001
AAA 002
AAA 003
AAA 004'''

    other = '''
AAA 001
AAA 002
AAA 003
AAA 004'''

    new = '''
AAA 001
AAA 002
AAA 003
AAA 005'''

    expected = '''
AAA 001
AAA 002
AAA 003
AAA 005'''

    eq_(merge(old, other, new), expected)


def test_only_two_changed():
    old = 'AAA 001\nAAA 002'
    other = 'AAA 001\nAAA 001\nAAA 002'
    new = 'AAA 001\nAAA 002'
    expected = '''AAA 001
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
AAA 001
AAA 002
========================================
AAA 002
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'''
    eq_(merge(old, other, new), expected)


def test_convert_old_new_to_list():
    # the arguments for old, other and new can be lists of lines too.
    old = ('AAA 001',)
    other = ('AAA 002',)
    new = ('AAA 001',)
    expected = '''<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
AAA 002
========================================
AAA 001
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'''
    eq_(merge(old, other, new), expected)


def test_other_and_new_changed():
    old = 'AAA 001\nAAA 002'
    other = 'AAA 002\nAAA 001'
    new = 'B2\nB52'
    expected = '''<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
AAA 002
AAA 001
========================================
B2
B52
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'''
    eq_(merge(old, other, new), expected)


def test_new_changed_other_unchanged():
    old = 'AAA 001\nAAA 002'
    other = 'AAA 001\nAAA 002'
    new = 'AAA 002'
    expected = 'AAA 002'
    eq_(merge(old, other, new), expected)


def test_new_and_other_changed():
    old = 'AAA 001\nAAA 001'
    other = 'AAA 001\nAAA 002'
    new = 'AAA 002'
    expected = '''<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
AAA 001
AAA 002
========================================
AAA 002
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'''
    eq_(merge(old, other, new), expected)


def test_nochange():
    other = new = old = 'AAA 002\nAAA04'
    expected = 'AAA 002\nAAA04'
    eq_(merge(old, other, new), expected)


def test_new_added_lines():
    old = 'AAA 002'
    other = 'AAA 002'
    new = 'Cool New\nFeature\nAAA 02'
    expected = 'Cool New\nFeature\nAAA 02'
    eq_(merge(old, other, new), expected)


def test_diffrenderer():
    a = u'Paul\nJust changed\nA bit'
    b = u'Paul\nJast changed\nA bit'
    udiff = generate_udiff(a, b)
    expected = [{
        'chunks': [[
            {
                'new_lineno': 1,
                'action': 'unmod',
                'line': u'Paul',
                'old_lineno': 1
            },
            {
                'new_lineno': u'',
                'action': 'del',
                'line': u'J<del>u</del>st changed',
                'old_lineno': 2
            },
            {
                'new_lineno': 2,
                'action': 'add',
                'line': u'J<ins>a</ins>st changed',
                'old_lineno': u''
            },
            {
                'new_lineno': 3,
                'action': 'unmod',
                'line': u'A bit',
                'old_lineno': 3
            }
        ]],
        'old_revision': None,
        'new_revision': None,
        'filename': None
    }]
    eq_(DiffRenderer(udiff, True).prepare(), expected)

    # test that diff renderer can extract the hg revision and filename
    # This tests also for some broken udiff workarounds.
    udiff = u'''
Those are lines
that are
not counted
--- a/test1.py Tue May 25 22:04:11 2010 +0200
+++ b/test1.py Thu May 27 21:08:19 2010 +0200
@@ -1,3 +1,3 @@
 Paul
-Just changed
+Jast changed
 A bit'''

    expected[0]['old_revision'] = u'Tue May 25 22:04:11 2010 +0200'
    expected[0]['new_revision'] = u'Thu May 27 21:08:19 2010 +0200'
    expected[0]['filename'] = u'a/test1.py'
    eq_(DiffRenderer(udiff, True).prepare(), expected)

    # prepare_udiff does the same as DiffRenderer(udiff).prepare()
    eq_(prepare_udiff(udiff, True), expected)
