# -*- coding: utf-8 -*-
"""
    inyoka.event.models
    ~~~~~~~~~~~~~~~~~~~

    Models for the event app.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import calendar
from datetime import datetime, timedelta
from inyoka.core.api import _, db
from inyoka.core.mixins import TextRendererMixin
from inyoka.core.auth.models import User
from inyoka.core.serializer import SerializableObject
from inyoka.forum.models import Question

class EventQuestionExtension(db.AttributeExtension):

    def append(self, state, answer, initiator):
        question = state.obj()
        db.atomic_add(question, 'answer_count', 1, primary_key_field='id')
        return answer

    def remove(self, state, answer, initiator):
        question = state.obj()
        db.atomic_add(question, 'answer_count', -1, primary_key_field='id')

class EventQuery(db.Query):

    def start_in(self, year, month):
        """Return a query for all events that start in the given year and month
        :param year: The year that the event starts have to match
        :param month: The month that the event starts have to match
        """
        days_in_month = calendar.monthrange(year, month)[1]
        interval_begin = datetime(year, month, 1, 0, 0, 0)
        interval_end = datetime(year, month, days_in_month, 23, 59, 59)
        q = self.filter(db.and_(
            Event.start_date >= interval_begin,
            Event.start_date <= interval_end
        )).order_by(Event.start_date)
        return q

    def end_in(self, year, month):
        """Return a query for all events that start in the given year and month
        :param year: The year that the event ends have to match
        :param month: The month that the event ends have to match
        """
        days_in_month = calendar.monthrange(year, month)[1]
        interval_begin = datetime(year, month, 1, 0, 0, 0)
        interval_end = datetime(year, month, days_in_month, 23, 59, 59)
        q = self.filter(db.and_(
            Event.end_date >= interval_begin,
            Event.end_date <= interval_end
        )).order_by(Event.end_date)
        return q

    def oncoming(self, year, month, duration=10):
        """Return a query for all events that start in the given year and month
        :param year: The year that the event starts have to match
        :param month: The month that the event starts have to match
        :param duration: The number of days from event start
        """
        interval_begin = datetime(year, month, 1, 0, 0, 0)
        interval_end = interval_begin + timedelta(duration)
        q = self.filter(db.and_(
            Event.start_date >= interval_begin,
            Event.start_date <= interval_end
        )).order_by(Event.start_date)
        return q


class Event(db.Model, SerializableObject, TextRendererMixin):
    __tablename__ = 'event_event'
    __mapper_args__ = {'extension': db.SlugGenerator('slug', 'title')}
    # To order all queries by default, something like
    # __mapper_args__ = {'order_by':Event.start_date.asc()
    # has to be added to this class. No idea how to do that, now

    query = db.session.query_property(EventQuery)

    # serializer properties
    object_type = 'event.event'
    public_fields = ('id', 'title', 'slug', 'text', 'author', 'start', 'end',
                     'discussion_question_id', 'info_question_id')

    #: Model columns
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(100), nullable=False)
    slug = db.Column(db.Unicode(100), unique=True, index=True)
    _text = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.ForeignKey(User.id), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    discussion_question_id = db.Column(db.Integer, db.ForeignKey(Question.id), nullable=True)
    info_question_id = db.Column(db.Integer, db.ForeignKey(Question.id), nullable=True)

    author = db.relationship(User, lazy='joined')
    #: TODO These relationships do not work yet. Could not find a manual how to create
    # a Question-object in a predefined Forum-object and link that Question to the
    # discussion_question_id- or info-question-attribute.

    # discussion_question = db.relationship(Question,
    #        backref=db.backref('event_event', uselist=False),
    #        primaryjoin=(discussion_question_id == Question.id))
    # info_question = db.relationship(Question,
    #        backref=db.backref('event_event', uselist=False),
    #        primaryjoin=(info_question_id == Question.id))

    # revision model implementation

    def get_url_values(self, action='view'):
        values = {
            'view': 'event/view',
            'edit': 'admin/event/edit',
        }
        return values[action], {'id': self.id}

    def __unicode__(self):
        return self.title
