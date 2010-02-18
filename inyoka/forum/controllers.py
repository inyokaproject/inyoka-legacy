# -*- coding: utf-8 -*-
"""
    inyoka.forum.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the forum app.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.forum.models import Forum, Question, Answer, Tag, question_tag, forum_tag
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
        Rule('/forum/<string:slug>/', endpoint='forum'),
        Rule('/forum/<string:forum>/ask/', endpoint='ask'),
        Rule('/questions/', endpoint='questions'),
        Rule('/question/<string:slug>/', endpoint='question'),
        Rule('/questions/tagged/<string:tags>/', endpoint='questions'),
        Rule('/ask/', endpoint='ask'),
        Rule('/get_tags/', endpoint='get_tags'),
    ]

    @view('index')
    @templated('forum/index.html')
    def index(self, request):
        forums = Forum.query.filter_by(parent=None).all()
        return {
           'forums': forums
        }

    @view('forum')
    @templated('forum/questions.html')
    def forum(self, request, slug, sort='newest', page=1):
        forum = Forum.query.filter_by(slug=slug).first()
        query = Question.query.filter(db.and_(
                Question.id == question_tag.c.question_id,
                question_tag.c.tag_id.in_(t.id for t in forum.tags)))

        if sort == 'newest':
            query = query.order_by(Question.date_asked.desc())
        elif sort == 'active':
            query = query.filter(Answer.question_id == Question.id) \
                         .order_by(Answer.date_answered)
        pagination = URLPagination(query, page)
        return {
           'forum': forum,
           'questions': pagination.query,
           'pagination': pagination.buttons()
        }


    @view('questions')
    @templated('forum/questions.html')
    def questions(self, request, tags=None, sort='newest'):
        if not tags:
            qry = Question.query
        else:
            tags = filter(bool, (Tag.query.filter_by(name=t).one() \
                          for t in tags.split()))
            qry = Question.query.filter(db.and_(
                        Question.id == question_tag.c.question_id,
                        question_tag.c.tag_id.in_(t.id for t in tags)))

        if sort == 'newest':
            questions = qry.order_by(Question.date_asked.desc())
        return {
            'tags': tags,
            'questions': questions[:50]
        }

    @view('question')
    @templated('forum/question.html')
    def question(self, request, slug):
        question = Question.query.filter_by(slug=slug).one()
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
            'question': question,
            'form': form.as_widget()
        }

    @view('ask')
    @templated('forum/ask.html')
    def ask(self, request, forum=None):
        form = AskQuestionForm()
        if forum:
            forum = Forum.query.filter_by(slug=forum).one()
            form.data['tags'] = ' '.join(t.name for t in forum.tags)
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

