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
from datetime import datetime, timedelta
from random import randrange, choice, random, shuffle
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from jinja2.utils import generate_lorem_ipsum
from inyoka.core.api import db


# one of small, medium or large
SIZE = 'small'

USERNAMES = '''
    asanuma bando chiba ekiguchi erizawa fukuyama inouye ise jo kanada
    kaneko kasahara kasuse kazuyoshi koyama kumasaka matsushina
    matsuzawa mazaki miwa momotami morri moto nakamoto nakazawa obinata
    ohira okakura okano oshima raikatuji saigo sakoda santo sekigawa
    shibukji sugita tadeshi takahashi takizawa taniguchi tankoshitsu
    tenshin umehara yamakage yamana yamanouchi yamashita yamura
    aebru aendra afui asanna callua clesil daev danu eadyel eane efae
    ettannis fisil frudali glapao glofen grelnor halissa iorran oamira
    oinnan ondar orirran oudin paenael
'''.split()

TAGS = '''
    ajhar amuse animi apiin azoic bacon bala bani bazoo bear bloom bone
    broke bungo burse caam cento clack clear clog coyly creem cush deity
    durry ella evan firn grasp gype hance hanky havel hunks ingot javer
    juno kroo larix lift luke malo marge mart mash nairy nomos noyau
    papey parch parge parka pheal pint poche pooch puff quit ravin ream
    remap rotal rowen ruach sadhu saggy saura savor scops seat sere
    shone shorn sitao skair skep smush snoop soss sprig stalk stiff
    stipa study swept tang tars taxis terry thirt ulex unkin unmix unsin
    uprid vire wally wheat woven xylan
'''.split()

EPOCH = datetime(1930, 1, 1)

_highest_date = EPOCH

def get_date(last=None):
    global _highest_date
    secs = randrange(10, 120)
    d = (last or EPOCH) + timedelta(seconds=secs)
    if _highest_date is None or d > _highest_date:
        _highest_date = d
    return d


def create_test_users():
    from inyoka.core.auth.models import User, UserProfile, Group

    # admin user
    admin = User(u'admin', u'root@localhost', u'default')
    admin_profile = UserProfile(user=admin)

    # some crazy users
    user_instances = []
    users = {
        u'apollonier':       (u'apollonier@crazynickname.com', u'rocket!'),
        u'tux der große':    (u'tuxi@grossi.de', u'pinguin'),
        u'quaki':            (u'ente@teich.zo', u'fluss'),
        u'dummuser':         (u'dumm@user.co', u'dumm?')
    }
    for user in users:
        u = User(user, *users[user])
        p = UserProfile(user=u, real_name=u'Some Realname', location=u'Germany')
        user_instances.append(u)

    db.session.commit()

    team = Group(name=u'Team')
    webteam = Group(name=u'Webteam', parents=set([team]), users=user_instances[:3])
    supporter = Group(name=u'Supporter', parents=set([team]))
    multimedia = Group(name=u'Supporter Multimedia', parents=set([supporter]))
    db.session.commit()

    # create some stub and dummy users...
    num = {'small': 15, 'medium': 30, 'large': 50}[SIZE]
    used = set()
    for x in xrange(num):
        while 1:
            username = choice(USERNAMES)
            if username not in used:
                used.add(username)
                break
        u = User(username, '%s@example.com' % username, 'default')
        UserProfile(user=u)
    db.session.commit()


def create_stub_tags():
    from inyoka.core.models import Tag
    num = {'small': 10, 'medium': 20, 'large': 50}[SIZE]
    used = set()
    for x in xrange(randrange(num - 5, num + 5)):
        while 1:
            tag = choice(TAGS)
            if tag not in used:
                used.add(tag)
                obj = Tag(name=tag)
                break
    db.session.commit()


def create_forum_test_data():
    from inyoka.forum.models import Tag, Forum, Question, Answer, Vote, Entry
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

    tags = Tag.query.all()
    users = User.query.all()
    last_date = None

    num, var = {'small': (50, 10), 'medium': (200, 20),
                'large': (1000, 200)}[SIZE]
    count = 0
    for x in xrange(randrange(num - var, num + var)):
        these_tags = list(tags)
        shuffle(these_tags)
        question = Question(title=generate_lorem_ipsum(1, False, 3, 9),
                            text=generate_lorem_ipsum(randrange(1, 5), False, 40, 140),
                            author=choice(users), date_created=get_date(last_date),
                            tags=these_tags[:randrange(2, 6)])
        last_date = question.date_created
    db.session.commit()

    # answers
    questions = Question.query.all()
    replies = {'small': 4, 'medium': 8, 'large': 12}[SIZE]
    answers = []
    last_date = questions[-1].date_created
    for question in questions:
        for x in xrange(randrange(2, replies)):
            answer = Answer(question=question, author=choice(users),
                text=generate_lorem_ipsum(randrange(1, 3), False, 20, 100),
                date_created=get_date(last_date))
            answers.append(answer)
            last_date = answer.date_created

    db.session.commit()

    voted_map = set([])
    for answer in answers:
        for x in xrange(randrange(replies * 4)):
            answer = choice(answers)
            user = choice(users)
            if (user.id, answer.entry_id) not in voted_map:
                if random() >= 0.05:
                    v = Vote(score=+1, user=user)
                else:
                    v = Vote(score=-1, user=user)
                v.entry = Entry.query.get(answer.entry_id)
                voted_map.add((user.id, answer.entry_id))
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


def create_pastebin_test_data():
    from inyoka.core.auth.models import User
    from inyoka.paste.models import Entry
    u = User.query.get('admin')
    e1 = Entry(text=u'print "Hello World"', author=u, language='python')
    db.session.commit()
    e1.children.append(Entry(text=u'print "hello world"', author=u, language='python'))
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
        raw_text=u"Type:\n ./configure\n make\n '''make install'''\nThat\'s it.",
        change_user=u, change_comment=u'started installation page',
    )
    db.session.commit()


def rebase_dates():
    """Rebase all dates so that they are most recent."""
    from inyoka.forum.models import Entry
    entries = Entry.query.all()
    delta = datetime.utcnow() - _highest_date
    for entry in entries:
        entry.date_active += delta
        entry.date_created += delta
    db.session.commit()


def main():
    funcs = (create_test_users, create_stub_tags, create_forum_test_data, create_news_test_data,
             create_pastebin_test_data, create_wiki_test_data, rebase_dates)
    for func in funcs:
        print "execute %s" % func.func_name
        func()
    print "successfully created test data"


if __name__ == '__main__':
    main()
