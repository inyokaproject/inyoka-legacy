# -*- coding: utf-8 -*-
import datetime

from nose.tools import *

from inyoka.utils.text import gen_slug, gen_ascii_slug, gen_unicode_slug,\
                              gen_timestamped_slug, wrap

def test_slugs():
    text = u'I do have unicode charz: öäü'
    eq_(gen_slug(text),gen_unicode_slug(text))
    eq_(gen_slug(text, ascii=True), gen_ascii_slug(text))

    eq_(gen_unicode_slug(text), u'i-do-have-unicode-charz:-\xf6\xe4\xfc')
    # shouldn't non ascii get split out?
    eq_(gen_ascii_slug(text + ' at least I did'), u'i-do-have-unicode-charz:-at-least-i-did')

def test_timestamped_slugs():
    text = u'my new slug'
    pub_date = datetime.datetime(2009, 10, 12, 8, 3)
    eq_(gen_timestamped_slug(text, 'entry', pub_date), u'2009/10/12/my new slug')

    eq_(gen_timestamped_slug(text, 'entry', pub_date, url_format='%fail%'), '%fail%')

    eq_(gen_timestamped_slug(text, 'post', pub_date), u'my new slug')

def test_wrap():
    msg = """Arthur:  "The Lady of the Lake, her arm clad in the purest \
shimmering samite, held aloft Excalibur from the bosom of the water, \
signifying by Divine Providence that I, Arthur, was to carry \
Excalibur. That is why I am your king!"

Dennis:  "Listen. Strange women lying in ponds distributing swords is \
no basis for a system of government. Supreme executive power derives \
from a mandate from the masses, not from some farcical aquatic \
ceremony!\""""

    result = """Arthur:  "The Lady of the Lake, her arm
clad in the purest shimmering samite,
held aloft Excalibur from the bosom of
the water, signifying by Divine
Providence that I, Arthur, was to carry
Excalibur. That is why I am your king!"

Dennis:  "Listen. Strange women lying in
ponds distributing swords is no basis
for a system of government. Supreme
executive power derives from a mandate
from the masses, not from some farcical
aquatic ceremony!\""""

    eq_(wrap(msg, 40), result)
