from nose.tools import *
from inyoka.core.api import db
from inyoka.core.models import User
from inyoka.utils.highlight import highlight_code
from inyoka.paste.models import Entry


def test_automatic_rendering():
    code1 = '@property\ndef(self, foo=None):\n    raise Exception\n'
    rendered_code1 = highlight_code(code1, 'python')
    code2 = 'import sys\nclass Example(object):\n    pass\n'
    rendered_code2 = highlight_code(code2, 'python')
    rendered_code2_plain = highlight_code(code2)
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

    def _my_rerender(self):
        raise AssertionError
    orig_rerender = Entry._rerender
    Entry._rerender = _my_rerender
    e.language = e.language
    e.code = e.code
    Entry._rerender = orig_rerender

def test_display_title():
    e1 = Entry('void', User.query.get('anonymous'), title=u'some paste')
    e2 = Entry('void', User.query.get('anonymous'))
    db.session.add_all((e1, e2))
    db.session.commit()
    eq_(e1.display_title, 'some paste')
    eq_(e2.display_title, '#%d' % e2.id)
