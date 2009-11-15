# -*- coding: utf-8 -*-
"""
    Test paste models

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from nose.tools import *
from inyoka.core.api import db
from inyoka.core.test import mock, tracker
from inyoka.core.models import User
from inyoka.utils.highlight import highlight_code
from inyoka.paste.models import Entry


def test_automatic_rendering():
    code1 = '@property\ndef(self, foo=None):\n    raise Exception\n'
    rendered_code1 = highlight_code(code1, 'python')
    code2 = 'import sys\nclass Example(object):\n    pass\n'
    rendered_code2 = highlight_code(code2, 'python')
    rendered_code2_plain = highlight_code(code2)

    # assert the model does rendering the right way
    e = Entry(code1, User.query.get('anonymous'), 'python')
    eq_(e.code, code1)
    eq_(e.rendered_code, rendered_code1)
    e.code = code2
    eq_(e.code, code2)
    eq_(e.rendered_code, rendered_code2)

    db.session.add(e)
    db.session.commit()

    e2 = Entry.query.get(e.id)
    eq_(e.language, 'python')
    eq_(e2.rendered_code, rendered_code2)
    e2.language = None
    eq_(e.language, None)
    eq_(e2.rendered_code, rendered_code2_plain)

    # assert that we don't call the rerender method when not required
    e2.language = 'python'
    eq_(e2.rendered_code, rendered_code2)
    mock('Entry._rerender', tracker=tracker)
    tracker.clear()
    e2.code = e2.code
    e2.language = e2.language
    assert_false(tracker.check('Called Entry._rerender()'))


def test_display_title():
    e1 = Entry('void', User.query.get('anonymous'), title=u'some paste')
    e2 = Entry('void', User.query.get('anonymous'))
    db.session.add_all((e1, e2))
    db.session.commit()
    eq_(e1.display_title, 'some paste')
    eq_(e2.display_title, '#%d' % e2.id)
    eq_(unicode(e1), 'some paste')
    eq_(unicode(e2), '#%d' % e2.id)
