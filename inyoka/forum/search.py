# -*- coding: utf-8 -*-
"""
    inyoka.forum.search
    ~~~~~~~~~~~~~~~~~~~

    Search provider of the forum application.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import db, href
from inyoka.core.search import SearchProvider
from inyoka.forum.models import Answer, Question
from inyoka.utils.xml import strip_tags


class AnswerSearchProvider(SearchProvider):
    name = 'answer'
    index = 'portal'
    _query = Answer.query.options(db.eagerload(Answer.question, Answer.author))

    def _prepare(self, answer):
        return {
            'id': answer.id,
            'text': strip_tags(answer.rendered_text),
            'date': answer.date_created.date(),
            'title': answer.question.title,
            'author': answer.author.username,
            'link': href(answer),
        }

    def prepare(self, ids):
        query = self._query.filter(Answer.entry_id.in_(ids))
        d = dict((a.id, self._prepare(a)) for a in query)
        for id in ids:
            yield d[int(id)]

    def prepare_all(self):
        for answer in db.select_blocks(self._query, Answer.id):
            yield answer.id, self._prepare(answer)


class QuestionSearchProvider(SearchProvider):
    name = 'question'
    index = 'portal'
    _query = Question.query.options(db.eagerload(Question.author))

    def _prepare(self, question):
        return {
            'id': question.id,
            'text': strip_tags(question.rendered_text),
            'date': question.date_created.date(),
            'author': question.author.username,
            'title': question.title,
            'link': href(question),
            'tag': question.tags,
        }

    def prepare(self, ids):
        query = self._query.filter(Question.id.in_(ids))
        d = dict((q.id, self._prepare(q)) for q in query)
        for id in ids:
            yield d[int(id)]

    def prepare_all(self):
        for question in db.select_blocks(self._query, Question.id):
            yield question.id, self._prepare(question)
