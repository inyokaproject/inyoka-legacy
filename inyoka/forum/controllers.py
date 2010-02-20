# -*- coding: utf-8 -*-
"""
    inyoka.forum.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the forum app.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.forum.models import Forum, Question, Answer, Tag, Vote, \
         question_tag, forum_tag
from inyoka.forum.forms import AskQuestionForm, AnswerQuestionForm
from inyoka.core.api import IController, Rule, view, service, templated, db, \
         redirect, redirect_to, href
from inyoka.utils.pagination import URLPagination
from inyoka.core.http import Response
from datetime import datetime


class ForumController(IController):
    name = 'forum'

    url_rules = [
        Rule('/', endpoint='index'),

        Rule('/questions/', endpoint='questions'),
        Rule('/questions/<any(newest, active, votes):sort>/', endpoint='questions'),
        Rule('/tagged/<string:tags>/', endpoint='questions'),
        Rule('/tagged/<string:tags>/<any(newest, active, votes):sort>/', endpoint='questions'),
        Rule('/forum/<string:forum>/', endpoint='questions'),
        Rule('/forum/<string:forum>/<any(newest, active, votes):sort>/', endpoint='questions'),

        Rule('/question/<string:slug>/', endpoint='question'),
        Rule('/question/<string:slug>/<string:sort>/', endpoint='question'),

        Rule('/ask/', endpoint='ask'),
        Rule('/forum/<string:forum>/ask/', endpoint='ask'),

        Rule('/get_tags/', endpoint='get_tags'),
    ]

    @view('index')
    @templated('forum/index.html')
    def index(self, request):
        forums = Forum.query.filter_by(parent=None).all()
        return {
           'forums': forums
        }

    @view('questions')
    @templated('forum/questions.html')
    def questions(self, request, forum=None, tags=None, sort='newest', page=1):
        query = Question.query

        # Filter by Forum or Tag (optionally)
        if forum:
            forum = Forum.query.filter_by(slug=forum).first()
            tags = forum.tags
        elif tags:
            tags = filter(bool, (Tag.query.filter_by(name=t).one() \
                          for t in tags.split()))
        if tags:
            query = query.filter(db.and_(
                        Question.id == question_tag.c.question_id,
                        question_tag.c.tag_id.in_(t.id for t in tags)))

        # Order by "newest", "active" or "votes"
        if sort == 'newest':
            query = query.order_by(Question.date_asked.desc())
        elif sort == 'active':
            query = query.order_by(Question.date_active.desc())
        elif sort == 'votes':
            query = query.order_by([Question.score.desc(),
                    Question.date_active.desc()])

        # Paginate results
        pagination = URLPagination(query, page=page)
        return {
            'forum': forum,
            'tags': tags or [],
            'questions': pagination.get_objects(),
            'sort': sort,
            'pagination': pagination
        }

    @view('question')
    @templated('forum/question.html')
    def question(self, request, slug, sort='votes', page=1):
        question = Question.query.filter_by(slug=slug).one()
        answer_query = Answer.query.filter_by(question=question)
        if sort == 'newest':
            answer_query = answer_query.order_by(Answer.date_answered.desc())
        elif sort == 'oldest':
            answer_query = answer_query.order_by(Answer.date_answered)
        pagination = URLPagination(answer_query, page=page)

        action = request.args.get('action')
        if action in ('vote-up', 'vote-down'):
            vote = Vote.query.filter_by(question=question, answer=None,
                    user=request.user).first()
            score = (action == 'vote-up' and 1 or -1)
            if not vote:
                vote = Vote(question=question, answer=None,
                        user=request.user, score=score)
                db.session.add(vote)
            else:
                vote.score = score
            db.session.commit()

        form = AnswerQuestionForm()
        if request.method == 'POST' and form.validate(request.form):
            answer = Answer(
                author=request.user,
                question=question,
                date_answered=datetime.utcnow(),
                text=form.data['text']
            )
            db.session.add(answer)
            db.session.commit()
            return redirect(href(question))

        return {
            'sort': sort,
            'question': question,
            'answers': pagination.get_objects(),
            'form': form.as_widget(),
            'pagination': pagination
        }

    @view('ask')
    @templated('forum/ask.html')
    def ask(self, request, forum=None):
        tags = []
        if request.args.get('tags'):
            tags = filter(bool, (Tag.query.filter_by(name=t).one() \
                          for t in request.args.get('tags').split()))
        elif forum:
            forum = Forum.query.filter_by(slug=forum).one()
            tags = forum.tags

        form = AskQuestionForm()
        form.data['tags'] = ' '.join(t.name for t in tags)

        if request.method == 'POST' and form.validate(request.form):
            question = Question(
                title=form.data['title'],
                author=request.user,
                date_asked=datetime.utcnow(),
                text=form.data['text'],
                tags=form.data['tags']
            )
            db.session.add(question)
            db.session.commit()
            return redirect_to(question)

        return {
            'forum': forum,
            'tags': tags,
            'form': form.as_widget()
        }


    @service('get_tags')
    def get_tags(self, request):
        q = request.args.get('q')
        if not q:
            tags = Tag.query.all()[:10]
        else:
            tags = Tag.query.filter(Tag.name.startswith(q))[:10]
        return list({'id': t.name, 'name': t.name} for t in tags)
