#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    create_testdata

    A script that is used to create some test data for easy testing.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from inyoka.core.api import db


def create_test_users():
    from inyoka.core.auth.models import User
    from inyoka.portal.models import UserProfile

    # admin user
    admin = User(u'admin', u'root@localhost', u'default')
    admin_profile = UserProfile(user=admin)

    # some crazy users
    users = {
        u'apollonier':       (u'apollonier@crazynickname.com', u'rocket!'),
        u'tux der große':    (u'tuxi@grossi.de', u'pinguin'),
        u'quaki':            (u'ente@teich.zo', u'fluss'),
        u'dummuser':         (u'dumm@user.co', u'dumm?')
    }
    for user in users:
        u = User(user, *users[user])
        p = UserProfile(user=u)

    db.session.commit()


def create_forum_test_data():
    from inyoka.forum.models import Tag, Forum, Question, Answer
    from inyoka.core.auth.models import User
    u1 = User.query.filter_by(username='dummuser').first()
    u2 = User.query.filter_by(username='quaki').first()

    # tags
    media = Tag(name=u'Media')
    hardware = Tag(name=u'Hardware & Zeugs')

    # forums
    support_forum = Forum(name=u'Support', description=u'Supportzeugs')
    media_forum = Forum(name=u'Media', description=u'Mediazeugs')
    hardware_forum = Forum(name=u'Hardware', description=u'Hardwarezeugs')
    support_forum.subforums = [media_forum, hardware_forum]

    db.session.commit()

    # questions
    q1 = Question(title=u'Mein Banshee geht nicht mehr!',
        text=u'Tia, steht halt im Titel :-)',
        author=u1, tags=[media])
    q2 = Question(title=u'PC putt',
        text=u'Wenn ihr noch Infos braucht, sagt welche',
        author=u1, tags=[hardware])

    a1 = Answer(question=q2, author=u2,
        text=u'Schmeiß ihn weg, hillft definitiv!')
    db.session.commit()



def main():
    funcs = (create_test_users, create_forum_test_data)
    for func in funcs:
        print "execute %s" % func.func_name
        func()
    print "successfully created test data"


if __name__ == '__main__':
    main()
