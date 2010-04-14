# -*- coding: utf-8 -*-
"""
    inyoka.forum.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the forum app.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.forum.models import Forum, Question, Answer, Tag, Vote, \
         question_tag, forum_tag, Entry
from inyoka.forum.forms import AskQuestionForm, AnswerQuestionForm
from inyoka.core.api import IController, Rule, view, service, templated, db, \
         redirect, redirect_to, href
from inyoka.utils.pagination import URLPagination
from inyoka.core.http import Response


def context_modifier(request, context):
    context.update(
        active='forum'
    )


class ForumController(IController):
    name = 'forum'

    url_rules = [
        Rule('/', endpoint='index'),

        Rule('/questions/', endpoint='questions'),
        Rule('/questions/<any(latest, active, unanswered, votes):sort>/',
             endpoint='questions'),
        Rule('/tagged/<string:tags>/', endpoint='questions'),
        Rule('/tagged/<string:tags>/<any(latest, active, unanswered, votes):sort>/',
             endpoint='questions'),
        Rule('/forum/<string:forum>/', endpoint='questions'),
        Rule('/forum/<string:forum>/<any(latest, active, unanswered, votes):sort>/',
             endpoint='questions'),

        Rule('/question/<string:slug>/', endpoint='question'),
        Rule('/question/<string:slug>/<string:sort>/', endpoint='question'),

        Rule('/vote/<int:entry_id>/<string:action>/',
            endpoint='vote'),

        Rule('/ask/', endpoint='ask'),
        Rule('/forum/<string:forum>/ask/', endpoint='ask'),
    ]

    @view('index')
    @templated('forum/index.html', modifier=context_modifier)
    def index(self, request):
        forums = Forum.query.filter_by(parent=None).all()
        return {
           'forums': forums
        }

    @view('questions')
    @templated('forum/questions.html', modifier=context_modifier)
    def questions(self, request, forum=None, tags=None, sort='latest', page=1):
        query = Question.query.options(db.joinedload('answers'))

        # Filter by Forum or Tag (optionally)
        if forum:
            forum = Forum.query.filter_by(slug=forum).first()
            query = query.forum(forum)
            tags = forum.all_tags
        elif tags:
            tags = filter(bool, (Tag.query.filter_by(name=t).one() \
                          for t in tags.split()))
            query = query.tagged(tags)

        # Order by "latest", "active", "unanswered" or "votes"
        query = getattr(query, sort)

        # Paginate results
        pagination = URLPagination(query, page=page)
        return {
            'forum': forum,
            'tags': tags or [],
            'questions': pagination.query,
            'sort': sort,
            'pagination': pagination
        }

    @view('question')
    @templated('forum/question.html', modifier=context_modifier)
    def question(self, request, slug, sort='votes', page=1):
        question = Question.query.options(db.joinedload('author')) \
                                 .filter_by(slug=slug).one()
        answer_query = Answer.query.options(db.joinedload('votes')) \
                                   .filter_by(question=question)
        answer_query = getattr(answer_query, sort)
        pagination = URLPagination(answer_query, page=page)

        form = AnswerQuestionForm()
        if request.method == 'POST' and form.validate(request.form):
            answer = Answer(
                author=request.user,
                question=question,
                text=form.data['text'],
            )
            db.session.commit()
            return redirect(href(question))

        # increase counters
        question.touch()

        # precalculate user votes
        answers = pagination.get_objects()
        user_votes = {question.id: question.get_vote(request.user)}
        for answer in answers:
            vote = [vote for vote in answer.votes
                    if vote.user.id == request.user.id]
            user_votes[answer.id] = vote and vote[0] or None

        return {
            'sort': sort,
            'question': question,
            'answers': pagination.get_objects(),
            'form': form.as_widget(),
            'pagination': pagination,
            'user_votes': user_votes
        }

    @view('ask')
    @templated('forum/ask.html', modifier=context_modifier)
    def ask(self, request, forum=None):
        tags = []
        if request.args.get('tags'):
            tags = filter(bool, (Tag.query.filter_by(name=t).one() \
                          for t in request.args.get('tags').split()))
        elif forum:
            forum = Forum.query.filter_by(slug=forum).one()
            tags = forum.tags

        form = AskQuestionForm(initial={'tags': tags})

        if request.method == 'POST' and form.validate(request.form):
            question = Question(
                title=form.data['title'],
                author=request.user,
                text=form.data['text'],
                tags=form.data['tags']
            )
            db.session.commit()
            return redirect_to(question)

        return {
            'forum': forum,
            'tags': tags,
            'form': form.as_widget()
        }

    @view
    def vote(self, request, entry_id, action):
        entry = Entry.query.get(entry_id)
        v = Vote.query.filter_by(entry=entry, user=request.user).first()
        args = {
            'up':           {'score': +1},
            'down':         {'score': -1},
            'revoke':       {'score':  0},
            'favorite':     {'favorite': True},
            'nofavorite':   {'favorite': False}
        }[action]
        if not v:
            args.update({
                'score': args.get('score', 0),
                'user': request.user,
            })
            v = Vote(**args)
            v.entry = entry
        else:
            for key, a in args.iteritems():
                setattr(v, key, a)
        db.session.commit()
        return redirect_to(entry)
