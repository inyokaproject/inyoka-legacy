# -*- coding: utf-8 -*-
"""
    Test paste models

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core.auth.models import User
from inyoka.utils.highlight import highlight_text
from inyoka.paste.models import Entry


def test_automatic_rendering():
    text1 = '@property\ndef(self, foo=None):\n    raise Exception\n'
    rendered_text1 = highlight_text(text1, 'python')
    text2 = 'import sys\nclass Example(object):\n    pass\n'
    rendered_text2 = highlight_text(text2, 'python')
    rendered_text2_plain = highlight_text(text2)

    # assert the model does rendering the right way
    e = Entry(text=text1, author=User.query.get_anonymous(), language='python')
    eq_(e.text, text1)
    eq_(e.rendered_text, rendered_text1)
    e.text = text2
    eq_(e.text, text2)
    eq_(e.rendered_text, rendered_text2)

    db.session.commit()

    e2 = Entry.query.get(e.id)
    eq_(e.language, 'python')
    eq_(e2.rendered_text, rendered_text2)
    e2.language = None
    eq_(e.language, None)
    eq_(e2.rendered_text, rendered_text2_plain)

    # assert that we don't call the rerender method when not required
    e2.language = 'python'
    eq_(e2.rendered_text, rendered_text2)
    mock('Entry._render', tracker=tracker)
    tracker.clear()
    e2.text = e2.text
    e2.language = e2.language
    assert_false(tracker.check('Called Entry._render()'))


def get_data_callback(title=None):
    def callback():
        data = {
            'author': User.query.get_anonymous(),
            'text': 'void'
        }
        if title is not None:
            data['title'] = title
        return data
    return callback


class TestEntryModel(TestSuite):

    fixtures = {
        'pastes': [
            fixture(Entry, get_data_callback(u'some paste')),
            fixture(Entry, get_data_callback()),
    ]}

    @with_fixtures('pastes')
    def test_display_title(self, fixtures):
        e1, e2 = fixtures['pastes']
        eq_(e1.display_title, 'some paste')
        eq_(e2.display_title, 'Paste #%d' % e2.id)
        eq_(unicode(e1), 'some paste')
        eq_(unicode(e2), 'Paste #%d' % e2.id)
