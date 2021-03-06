#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    create_testdata

    A script that is used to create some test data for easy testing.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import sys
import math
from datetime import datetime, timedelta
from random import randrange, choice, random, shuffle, randint
from itertools import chain, islice, izip
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from jinja2.utils import generate_lorem_ipsum
from inyoka.core.api import db, href

_link_file = None


# one of small, medium or large
SIZE = 'small'

USERNAMES = u'''
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

LEADINS = u'''To characterize a linguistic level L,
    On the other hand,
    This suggests that
    It appears that
    Furthermore,
    We will bring evidence in favor of the following thesis:
    To provide a constituent structure for T(Z,K),
    From C1, it follows that
    For any transformation which is diversified in application to be of any interest,
    Analogously,
    Clearly,
    Note that
    Of course,
    Suppose, for instance, that
    Thus
    With this clarification,
    Conversely,
    We have already seen that
    By combining adjunctions and certain deformations,
    I suggested that these results would follow from the assumption that
    If the position of the trace in (99c) were only relatively inaccessible to movement,
    However, this assumption is not correct, since
    Comparing these examples with their parasitic gap counterparts, we see that
    In the discussion of resumptive pronouns following (81),
    So far,
    Nevertheless,
    For one thing,
    Summarizing, then, we assume that
    A consequence of the approach just outlined is that
    Presumably,
    On our assumptions,
    It may be, then, that
    It must be emphasized, once again, that
    Let us continue to suppose that
    Notice, incidentally, that '''

SUBJECTS = u''' the notion of level of grammaticalness
    a case of semigrammaticalness of a different sort
    most of the methodological work in modern linguistics
    a subset of English sentences interesting on quite independent grounds
    the natural general principle that will subsume this case
    an important property of these three types of EC
    any associated supporting element
    the appearance of parasitic gaps in domains relatively inaccessible to extraction
    the speaker-hearer's linguistic intuition
    the descriptive power of the base component
    the earlier discussion of deviance
    this analysis of a formative as a pair of sets of features
    this selectionally introduced ctxual feature
    a descriptively adequate grammar
    the fundamental error of regarding functional notions as categorial
    relational information
    the systematic use of complex symbols
    the theory of syntactic features developed earlier'''

VERBS = u'''can be defined in such a way as to impose
    delimits
    suffices to account for
    cannot be arbitrary in
    is not subject to
    does not readily tolerate
    raises serious doubts about
    is not quite equivalent to
    does not affect the structure of
    may remedy and, at the same time, eliminate
    is not to be considered in determining
    is to be regarded as
    is unspecified with respect to
    is, apparently, determined by
    is necessary to impose an interpretation on
    appears to correlate rather closely with
    is rather different from'''

OBJECTS = u''' problems of phonemic and morphological analysis.
    a corpus of tokens upon which conformity has been defined by the utterance test.
    the traditional practice of grammarians.
    the levels of acceptability from fairly high (e.g. (99a)) to virtual gibberish.
    a stipulation to place the constructions into these various categories.
    a descriptive fact of scriptless alertness: <script>alert("Gotcha");</script>.
    a parasitic gap construction.
    the extended c-command discussed in connection with (34).
    the ultimate standard that determines the accuracy of any proposed grammar.
    the system of base rules exclusive of the lexicon.
    irrelevant intervening ctxs in selectional rules.
    nondistinctness in the sense of distinctive feature theory.
    a general convention regarding the forms of the grammar.
    an abstract underlying order of <blink>blinking quarks</blink>.
    an important distinction in language use.
    the requirement that branching is tolerated within the dominance scope of a symbol.
    the strong generative capacity of the theory.'''

TAGLIST = u'''
    africa   amsterdam   animals   architecture   art   august   australia   autumn
    baby   barcelona  beach   berlin   birthday   black   blackandwhite   blue   boston
    bw   california   cameraphone   camping   canada   canon   car   cat   cats
    chicago   china   christmas   church   city   clouds   color   concert   day
    dc   december   dog   england   europe   fall   family   festival   film
    florida   flower   flowers   food   france   friends   fun   garden   geotagged
    germany   girl   graffiti   green   halloween   hawaii   hiking   holiday   home
    honeymoon   hongkong   house   india   ireland   island   italy   japan   july
    june   kids   la   lake   landscape   light   live   london   macro   may   me
    mexico   mountain   mountains   museum   music   nature   new   newyork
    newyorkcity   newzealand   night   nikon   nyc   ocean   october   paris   park
    party   people   portrait   red   river   roadtrip   rock   rome   san
    sanfrancisco   scotland   sea   seattle   september   show   sky   snow   spain
    spring   street   summer   sun   sunset   sydney   taiwan   texas   thailand
    tokyo   toronto   travel   tree   trees   trip   uk   urban   usa   vacation
    vancouver   washington   water   wedding   white   winter   yellow   york   zoo
'''.split()


EPOCH = datetime(1930, 1, 1)

_highest_date = EPOCH


def chomsky(times=1, line_length=72):
    parts = []
    for part in (LEADINS, SUBJECTS, VERBS, OBJECTS):
        phraselist = map(unicode.strip, part.splitlines())
        shuffle(phraselist)
        parts.append(phraselist)
        if randint(0, 3) == 0:
            parts.append("\n\n")
    output = chain(*islice(izip(*parts), 0, times))
    return ' '.join(output)


def get_date(last=None):
    global _highest_date
    secs = randrange(10, (2 * 60 * 60))
    d = (last or EPOCH) + timedelta(seconds=secs)
    if _highest_date is None or d > _highest_date:
        _highest_date = d
    return d


def create_test_users():
    global _link_file
    from inyoka.core.auth.models import User, UserProfile, Group

    # admin user
    admin = User(username=u'admin', email=u'root@localhost', password=u'default')
    admin.status = u'normal'
    admin_profile = UserProfile(user=admin)

    # some crazy users
    user_instances = []
    users = {
        u'apollonier':      (u'apollonier@crazynickname.com', u'rocket!',
            {'real_name': u'Apollo der Große', 'location': u'Österreich'}),
        u'tux der große':   (u'tuxi@grossi.de', u'pinguin',
            {'real_name': u'Tuxorius', 'location': u'Österreich'}),
        u'quaki':           (u'ente@teich.zo', u'fluss',
            {'real_name': u'Quaki der ganz ganz Große', 'location': u'Germany'}),
        u'maxarian':        (u'maix@noprogramming.com', u'damn!',
            {'real_name': u'Marian Florianus', 'location': u'Berlin/Germany'}),
        u'dummuser':        (u'dumm@user.co', u'dumm?',
            {'real_name': u'Dummorius', 'location': u'/dev/zero'}),
        u'FedoraFlo':       (u'fed@f.lo', u'default',
            {'real_name': u'Florius Maximus', 'location': u'Frankfurt/Germany'}),
        u'lidnele':         (u'elen@d.il', u'default',
            {'real_name': u'Andreas Lilende', 'location': u'ubuntuusers.de'}),
        u'Kami':            (u'kam@i.xy', u'default',
            {'real_name': u'Aldaran Utama Putiran', 'location': u'Turkey'}),
        u'carost':          (u'ost@car.de', u'default',
            {'real_name': u'Tschaka Bam', 'location': u'Germany'}),
        u'The-Decompiler':  (u'no@compiler.xy', u'default',
            {'real_name': u'©æſðæ®€“”@', 'location': u'/dev/cdrom'}),
        u'guj':             (u'j@u.g', u'default',
            {'real_name': u'Yea Man', 'location': u'Germany'}),
        u'RoterRitter':     (u'roterr@it.er', u'default',
            {'real_name': u'Der Rote Ritter mit der langen Lanze', 'location': u'Burg Rotenstein'}),
        u'Kebap':           (u'dö@n.er', u'default',
            {'real_name': u'DönerDönerDönerDöner', 'location': u'Berlin'}),
    }
    for user in users:
        email, pw = users[user][:-1]
        u = User(username=user, email=email, password=pw)
        u.status = u'normal'
        p = UserProfile(user=u, **users[user][-1])
        user_instances.append(u)

    db.session.commit()

    team = Group(name=u'Team')
    webteam = Group(name=u'Webteam', parents=set([team]), users=user_instances[:4])
    supporter = Group(name=u'Supporter', parents=set([team]), users=user_instances[4:-2])
    multimedia = Group(name=u'Supporter Multimedia', parents=set([supporter]),
        users=user_instances[-2:])
    ikhayateam = Group(name=u'Ikhayateam', parents=set([team]))
    db.session.commit()

    # create some stub and dummy users...
    num = {'small': 15, 'medium': 30, 'large': 50}[SIZE]
    used = set()
    groups = [team, webteam, supporter, multimedia, ikhayateam]
    for x in xrange(num):
        while 1:
            username = choice(USERNAMES)
            if username not in used:
                used.add(username)
                break
        u = User(username=username, email=u'%s@example.com' % username,
                 password=u'default')
        UserProfile(user=u)
        if random() > 0.6:
            u.groups = [choice(groups)]
    db.session.commit()

    # store links for benchmark tests
    links = [href(u.profile, _external=True) for u in User.query.all()]
    links.extend([href(g, _external=True) for g in groups])
    _link_file.write(u'\n'.join(links))


def create_stub_tags():
    global _link_file
    from inyoka.core.models import Tag
    num = {'small': 10, 'medium': 25, 'large': 50}[SIZE]
    used = set()
    for x in xrange(randrange(num - 5, num + 5)):
        while 1:
            tag = choice(TAGLIST)
            if tag not in used:
                used.add(tag)
                obj = Tag(name=tag)
                break
    db.session.commit()

    links = [href(tag, _external=True) for tag in Tag.query.all()]
    _link_file.write(u'\n'.join(links))


def create_forum_test_data():
    global _link_file
    from inyoka.forum.models import Tag, Forum, Question, Answer, Vote, ForumEntry
    from inyoka.core.auth.models import User

    links = []

    u1 = User.query.filter_by(username=u'dummuser').first()
    u2 = User.query.filter_by(username=u'quaki').first()

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

    main_tags = [gnome, gtk, kde, qt, window_manager, hardware, inyoka, audio]

    # forums
    inyoka_forum = Forum(
        name=u'Inyoka Project',
        description=u'Please tell us your opinion about the new Inyoka!',
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

    tags = Tag.query.public().all()
    users = tuple(User.query.options(db.eagerload('groups')).all())
    last_date = None
    questions = []

    num, var = {'small': (50, 10), 'medium': (250, 50),
                'large': (1000, 200)}[SIZE]
    for x in xrange(randrange(num - var, num + var)):
        if random() >= 0.8:
            # we use them a bit more than others, to get a more realistic
            # tag usage.
            these_tags = main_tags
        else:
            these_tags = list(tags)
        shuffle(these_tags)
        question = Question(title=generate_lorem_ipsum(1, False, 3, 9),
                            text=chomsky(randint(0, 10) or 40),
                            author=choice(users), date_created=get_date(last_date),
                            tags=these_tags[:randrange(1, 6)])
        last_date = question.date_created
        questions.append(question)
    db.session.commit()

    links.extend([href(q, _external=True) for q in questions])

    # answers
    replies = {'small': 4, 'medium': 8, 'large': 12}[SIZE]
    answers = []
    last_date = questions[-1].date_created
    shuffle(questions)
    for question in questions[:randrange(len(questions))]:
        for x in xrange(randrange(2, replies)):
            answer = Answer(question=question, author=choice(users),
                text=chomsky(randint(0, 10) or 40),
                date_created=get_date(last_date))
            answers.append(answer)
            last_date = answer.date_created

    db.session.commit()

    voted_map = []
    objects = answers + questions
    for obj in objects[:randrange(len(objects))]:
        for x in xrange(randrange(2, replies * 4)):
            entry = choice(objects)
            user = choice(users)
            if (user.id, entry.entry_id) not in voted_map:
                if random() >= 0.2:
                    v = Vote(score=+1, user=user)
                elif random() >= 0.5:
                    v = Vote(score=-1, user=user)
                else:
                    break
                v.entry_id = entry.entry_id
                v.favorite = random() > 0.9
                entry.votes.append(v)
                voted_map.append((user.id, entry.entry_id))
        db.session.commit()

    _link_file.write(u'\n'.join(links))


def create_news_test_data():
    global _link_file
    from inyoka.core.auth.models import User
    from inyoka.news.models import Tag, Comment, Article
    users = User.query.all()
    tags = Tag.query.public().all()
    num = {'small': 10, 'medium': 50, 'large': 100}[SIZE]
    used = set()
    for x in xrange(randrange(num - 5, num + 5)):
        while 1:
            title = generate_lorem_ipsum(1, False, 3, 9)
            if title not in used:
                shuffle(tags)
                these_tags = tags[:randrange(2,6)]
                user = choice(users)
                article = Article(title=title,
                    intro=chomsky(randint(0, 5) or 10),
                    text=chomsky(randint(0, 100) or 200),
                    public=choice([True, False]), tags=these_tags,
                    author=user)
                used.add(title)
                break
    db.session.commit()

    _link_file.write(u'\n'.join([href(a, _external=True) for a in Article.query.all()]))

    # comments
    replies = {'small': 4, 'medium': 8, 'large': 12}[SIZE]
    articles = Article.query.all()
    for article in articles:
        for x in xrange(randrange(replies * 4)):
            article = choice(articles)
            user = choice(users)
            comment = Comment(text=chomsky(randint(0, 5) or 10),
                author=user, article=article)
    db.session.commit()


def create_pastebin_test_data():
    from inyoka.core.auth.models import User
    from inyoka.paste.models import PasteEntry
    u = User.query.get(u'admin')
    e1 = PasteEntry(text=u'print "Hello World"', author=u, language=u'python')
    db.session.commit()
    e1.children.append(PasteEntry(text=u'print "hello world"', author=u, language=u'python'))
    db.session.commit()


def rebase_dates():
    """Rebase all dates so that they are most recent."""
    from inyoka.forum.models import ForumEntry
    entries = ForumEntry.query.all()
    delta = datetime.utcnow() - _highest_date
    for entry in entries:
        entry.date_active += delta
        entry.date_created += delta
    db.session.commit()


def main():
    global _link_file
    _link_file = open('links.txt', 'w')
    funcs = (create_test_users, create_stub_tags, create_news_test_data,
             create_pastebin_test_data, create_forum_test_data,
             rebase_dates)
    for func in funcs:
        print "execute %s" % func.func_name
        func()
    _link_file.close()
    print "successfully created test data"


if __name__ == '__main__':
    main()
