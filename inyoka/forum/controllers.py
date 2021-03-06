# -*- coding: utf-8 -*-
"""
    inyoka.forum.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the forum app.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.forum.models import Forum, Question, Answer, Tag, Vote, \
         ForumEntry
from inyoka.forum.forms import AskQuestionForm, AnswerQuestionForm, EditForumForm
from inyoka.core.api import IController, Rule, view, templated, db, \
         redirect, redirect_to, href, login_required
from inyoka.core.exceptions import Forbidden
from inyoka.core.forms.utils import model_to_dict, update_model
from inyoka.utils.pagination import URLPagination
from itertools import ifilter


def context_modifier(request, context):
    context.update(
        active='forum'
    )


class ForumController(IController):
    name = 'forum'

    url_rules = [
        Rule('/', endpoint='index'),

        Rule('/questions/', endpoint='questions'),
        Rule('/questions/<int:page>/', endpoint='questions'),
        Rule('/questions/<any(latest, active, unanswered, votes):sort>/',
             endpoint='questions'),
        Rule('/questions/<any(latest, active, unanswered, votes):sort>/' \
             '<int:page>/', endpoint='questions'),

        Rule('/tagged/<string:tags>/', endpoint='questions'),
        Rule('/tagged/<string:tags>/<int:page>/', endpoint='questions'),
        Rule('/tagged/<string:tags>/' \
             '<any(latest, active, unanswered, votes):sort>/',
             endpoint='questions'),
        Rule('/tagged/<string:tags>/' \
             '<any(latest, active, unanswered, votes):sort>/<int:page>/',
             endpoint='questions'),

        Rule('/forum/<string:forum>/', endpoint='questions'),
        Rule('/forum/<string:forum>/<int:page>/', endpoint='questions'),
        Rule('/forum/<string:forum>/' \
             '<any(latest, active, unanswered, votes):sort>/',
             endpoint='questions'),
        Rule('/forum/<string:forum>/' \
             '<any(latest, active, unanswered, votes):sort>/<int:page>/',
             endpoint='questions'),
        Rule('/forum/<string:forum>/add/', endpoint='edit_forum'),
        Rule('/forum/<string:forum>/edit/', endpoint='edit_forum'),

        Rule('/question/<string:slug>/', endpoint='question'),
        Rule('/question/<string:slug>/<int:page>/', endpoint='question'),
        Rule('/question/<string:slug>/<any(votes, latest, oldest):sort>/', endpoint='question'),
        Rule('/question/<string:slug>/<any(votes, latest, oldest):sort>/<int:page>/',
             endpoint='question'),
        Rule('/post/<int:posting_id>/', endpoint='posting'),

        Rule('/vote/<int:entry_id>/<string:action>/', endpoint='vote'),

        Rule('/ask/', endpoint='ask'),
        Rule('/forum/<string:forum>/ask/', endpoint='ask'),

        Rule('/answer/<int:entry_id>/', endpoint='answer'),
        Rule('/answer/<int:entry_id>/<any(edit):action>/', endpoint='answer'),
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
        query = Question.query

        # Filter by Forum or Tag (optionally)
        if forum:
            forum = Forum.query.filter_by(slug=forum).first()
            query = query.forum(forum)
            tags = forum.all_tags
        elif tags:
            tags = (t.lower() for t in tags.split(','))
            tags = Tag.query.public().filter(Tag.slug.in_(tags)).all()
            query = query.tagged(tags)

        # Order by "latest", "active", "unanswered" or "votes"
        query = getattr(query, sort)

        # Paginate results
        pagination = URLPagination(query, page)
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
        question = Question.query.filter_by(slug=slug).one()
        answer_query = Answer.query.filter_by(question=question)

        # Order by "votes", "latest" or "oldest"
        answer_query = getattr(answer_query, sort)

        pagination = URLPagination(answer_query, page)

        form = AnswerQuestionForm(request.form)
        if form.validate_on_submit():
            answer = Answer(author=request.user,
                            question=question,
                            text=form.text.data)
            db.session.commit()
            return redirect(href(question))

        # increase counters
        question.touch()

        # precalculate user votes
        answers = pagination.query
        user_votes = Vote.query.get_user_votes_on(request.user.id,
                                                  [a.id for a in answers])

        return {
            'sort': sort,
            'question': question,
            'answers': pagination.query,
            'form': form,
            'pagination': pagination,
            'user_votes': user_votes
        }

    @view('posting')
    def posting(self, request, posting_id=None):
        entry = ForumEntry.query.get(posting_id)
        return redirect_to(entry)

    @login_required
    @view('ask')
    @templated('forum/ask.html', modifier=context_modifier)
    def ask(self, request, forum=None):
        tags = []
        if request.args.get('tags'):
            tags = ifilter(bool, (Tag.query.public().filter_by(slug=t).one() \
                          for t in request.args.get('tags').split()))
        elif forum:
            forum = Forum.query.filter_by(slug=forum).one()
            tags = forum.tags

        form = AskQuestionForm(request.form, tags=tags)

        if form.validate_on_submit():
            question = Question(
                title=form.title.data,
                author=request.user,
                text=form.text.data,
                tags=form.tags.data
            )
            db.session.commit()
            return redirect_to(question)

        return {
            'forum': forum,
            'tags': tags,
            'form': form
        }

    @view('answer')
    @templated('forum/answer.html', modifier=context_modifier)
    def answer(self, request, entry_id, action=None):
        answer = Answer.query.get(entry_id)
        if action == 'edit':
            form = AnswerQuestionForm(request.form, text=answer.text)
            if form.validate_on_submit():
                answer.text = form.text.data
                db.session.commit()
                return redirect_to(answer)
            return {
                'form': form
            }
        else:
            kwargs = {'_anchor': 'answer-%s' % answer.id}
            return redirect_to(answer.question, **kwargs)

    @login_required
    @view
    def vote(self, request, entry_id, action):
        entry = ForumEntry.query.get(entry_id)
        if entry.author == request.user:
            raise Forbidden
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

    @view
    @login_required
    @templated('forum/admin/forum.html')
    def edit_forum(self, request, forum=None):
        if forum:
            forum = Forum.query.filter_by(slug=forum).first()
            initial = model_to_dict(forum)
        else:
            forum = None
            initial = {}

        form = EditForumForm(request.form, **initial)

        if form.validate_on_submit():
            if forum:
                forum = update_model(forum, form,
                    ('name', 'slug', 'parent', 'description', 'tags'))
            else:
                forum = Forum(
                    name=form.name.data,
                    slug=form.slug.data,
                    parent=form.parent.data,
                    description=form.description.data,
                    tags=form.tags.data
                )
            db.session.commit()
            return redirect_to('forum/index')

        return {
            'forum': forum,
            'form': form,
        }
