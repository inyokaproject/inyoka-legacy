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
    e = Entry(code1, 'python', User.query.get('anonymous'))
    eq_(e.rendered_code, rendered_code1)
    e.code = code2
    eq_(e.rendered_code, rendered_code2)

    db.session.add(e)
    db.session.commit()

    e2 = Entry.query.get(e.id)
    eq_(e2.rendered_code, rendered_code2)
