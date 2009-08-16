#-*- coding: utf-8 -*-
"""
    test_antispam
    ~~~~~~~~~~~~~

    This module tests the anti spam capabilities of inyoka.  For now inyoka
    just recognizes too much links in a text as spam.  There are no other
    heuristics yet.

    :copyright: Copyright 2009 by Christopher Grebs.
    :license: GNU GPL.
"""
from inyoka.utils.antispam import is_spam


SPAM1 = '''
http://iamalink.xy
Fooobar Baz bammmmm!
mailto:bar@foobariscool.com
Fam Fam!'''

NO_SPAM1 = '''
This is just some http://cootest.xy
That shall not be treated as spam.'''

# 30 links are just treated like spam as well
TOO_MUCH_LINKS = '''
http://foo.xy http://bar.xy http://baz.yx
ftp://ber.xy http://snake.of
mailto:fo@bar.xy skype:fam@fo.xy
ssh://root@opendoor.com
irc://19234612 file:///root/.secret''' * 3


def test_is_spam():
    assert is_spam(SPAM1) is True
    assert is_spam(NO_SPAM1) is False
    assert is_spam(TOO_MUCH_LINKS) is True
