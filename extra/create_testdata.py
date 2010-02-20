# -*- coding: utf-8 -*-
"""
    create_testdata

    A script that is used to create some test data for easy testing.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import db


def create_test_users():
    from inyoka.core.auth.models import User
    from inyoka.portal.models import UserProfile

    # admin user
    admin = User(u'admin', u'root@localhost', u'default')
    admin_profile = UserProfile(user=admin)

    # some crazy users
    users = {
        'apollonier':       (u'apollonier@crazynickname.com', u'rocket!'),
        'tux der große':    (u'tuxi@grossi.de', u'pinguin'),
        'quaki':            (u'ente@teich.zo', u'fluss')
    }
    for user in users:
        u = User(*users[user])
        p = UserProfile(user=u)

    db.session.commit()


def main():
    funcs = (create_test_users,)
    for func in funcs:
        print "execute %s" % func.func_name
        func()
    print "successfully created test data"


if __name__ == '__main__':
    main()
