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
         redirect, href
from inyoka.core.http import Response
from datetime import datetime


class ForumController(IController):
    name = 'forum'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/forum/<string:slug>/', endpoint='forum'),
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
    def forum(self, request, slug):
        forum = Forum.query.filter_by(slug=slug).first()
        questions = Question.query.filter(db.and_(
                Question.id == question_tag.c.question_id,
                question_tag.c.tag_id.in_(t.id for t in forum.tags))) \
                .order_by(Question.date_asked.desc())
        return {
           'forum': forum,
           'questions': questions
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
    def ask(self, request):
        form = AskQuestionForm()
        if request.method == 'POST' and form.validate(request.form):
            tags = []
            for tagname in form.data['tags']:
                tag = Tag.query.filter_by(name=tagname).first()
                if not tag:
                    # XXX: Disable automatic tag creation
                    tag = Tag(tagname)
                    db.session.add(tag)
                tags.append(tag)
            question = Question(
                title=form.data['title'],
                author=request.user,
                date_asked=datetime.utcnow(),
                text=form.data['text'],
                tags=tags
            )
            db.session.add(question)
            db.session.commit()
            return redirect(href('forum/index'))

        return {
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

