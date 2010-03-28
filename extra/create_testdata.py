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
from datetime import datetime
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
    gnome = Tag(name=u'GNOME')
    gtk = Tag(name=u'GTK')
    kde = Tag(name=u'KDE')
    qt = Tag(name=u'QT')
    window_manager = Tag(name=u'Window-Manager')
    hardware = Tag(name=u'Hardware')
    inyoka = Tag(name=u'Inyoka')
    audio = Tag(name=u'Audio')
    db.session.commit()

    # forums
    inyoka_forum = Forum(
        name=u'Inyoka Project',
        description=u'Please tell us our opinion about the new Inyoka!',
        tags=[inyoka])
    gnome_forum = Forum(
        name=u'The GNOME Desktop (Ubuntu)',
        description=u'Here you can find all GNOME and GTK related questions.',
        tags=[gnome, gtk])
    kde_forum = Forum(
        name=u'KDE Plasma (Kubuntu)',
        description=u'Everything about KDE, the desktop environment of Kubuntu.',
        tags=[kde, qt])
    window_manager_forum = Forum(
        name=u'Desktop Environments and Window Managers',
        description=u'Aks everything about GNOME, KDE or any other exotic window manager here',
        subforums=[gnome_forum, kde_forum],
        tags=[window_manager])
    hardware_forum = Forum(
        name=u'Hardware Problems',
        description=u'Describe your hardware problems here',
        tags=[hardware])
    db.session.commit()

    # questions
    q1 = Question(
        title=u'Which deskop environment should I choose?',
        text=u'Is GNOME or KDE the better choice? What do you think?',
        author=u1, tags=[gnome, kde])
    q2 = Question(
        title=u'Is there a good audio player like Amorok for GNOME?',
        text=u'I hate the KDE design, so is there any good audio player for GNOME?',
        author=u1, tags=[gnome, audio])
    q3 = Question(
        title=u'What do you like most about Inyoka?',
        text=u'Please, be honest!',
        author=u2, tags=[inyoka])
    db.session.commit()

    # answers
    q1a1 = Answer(
        question=q1,
        text=u'I use GNOME because I like it.',
        author=u2,
        date_created=datetime.utcnow())
    db.session.commit()


def create_news_test_data():
    from inyoka.core.auth.models import User
    from inyoka.news.models import Tag, Comment, Article
    u = User.query.filter_by(username=u'quaki').one()
    u2 = User.query.filter_by(username=u'dummuser').one()
    u3 = User.query.filter_by(username=u'tux der große').one()
    t1 = Tag(name=u'Ubuntu')
    t2 = Tag(name=u'Ubuntuusers')

    a1 = Article(title=u'Mein Ubuntu rockt!',
        intro=(u'Naja, mein Ubuntu rockt halt einfach und ich bin der'
               u' Meinung, \ndas das so bleiben sollte!'),
        text=(u'Und da ihr alle so cool seit und tschaka baam seit'
              u' verwendet ihr auch alle Ubuntu!!!'),
        public=True, tag=t1, author=u)

    db.session.commit()

    c1 = Comment(text=u'Find ich nicht so!', author=u2, article=a1)
    c2 = Comment(text=u'Ach, du spinnst doch!', author=u3, article=a1)
    db.session.commit()


def create_wiki_test_data():
    from inyoka.core.api import ctx
    from inyoka.core.auth.models import User
    from inyoka.wiki.models import Page, Revision

    u = User.query.first()
    a = Revision(
        page=Page(ctx.cfg['wiki.index.name']),
        raw_text=u'This is the wiki index page!',
        change_user=u, change_comment=u'hello world.',
    )

    b = Revision(
        page=Page(u'Installation'),
        raw_text=u'Type:\n ./configure\n make\n make install\nThat\'s it.',
        change_user=u, change_comment=u'started installation page',
    )
    db.session.commit()

def main():
    funcs = (create_test_users, create_forum_test_data, create_news_test_data,
             create_wiki_test_data)
    for func in funcs:
        print "execute %s" % func.func_name
        func()
    print "successfully created test data"


if __name__ == '__main__':
    main()
