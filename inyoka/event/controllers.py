# -*- coding: utf-8 -*-
"""
    inyoka.event.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the event app.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import calendar
from datetime import datetime, date, timedelta
from inyoka.core import exceptions as exc
from inyoka.core.api import IController, Rule, view, Response, \
    templated, db, redirect_to, Tag
from inyoka.utils.pagination import URLPagination
from inyoka.event.forms import AddEventForm
from inyoka.event.models import Event
from inyoka.forum.models import Question
from itertools import ifilter


def context_modifier(request, context):
    context.update(
        active='event'
    )

def daterange(start, end):
    for n in xrange((end - start).days):
        yield start + timedelta(n)

def validate_year(year):
    if not year or year < 1970:
        year = year or date.today().year
    return year

def validate_month(month):
    if not month or month < 1 or month > 12:
        month = date.today().month
    return month

class EventController(IController):
    name = 'event'

    url_rules = [
        Rule('/', endpoint='index'),
        Rule('/event/<int:id>/', endpoint='view'),
        Rule('/calendar/', endpoint='calendar'),
        Rule('/calendar/<int:year>/', endpoint='calendar'),
        Rule('/calendar/<int:year>/<int:month>/', endpoint='calendar'),
        Rule('/oncoming/', endpoint='oncoming'),
        Rule('/oncoming/<int:year>/', endpoint='oncoming'),
        Rule('/oncoming/<int:year>/<int:month>/', endpoint='oncoming'),
    ]

    @view
    @templated('event/index.html', modifier=context_modifier)
    def index(self, request):
        tags = []
        if request.args.get('tags'):
            tags = ifilter(bool, (Tag.query.public().filter_by(name=t).one() \
                          for t in request.args.get('tags').split()))

        form = AddEventForm(request.form)
        if form.validate_on_submit():
            # TODO request the form data
            #: Check for creating a question-object a discussion
            if form.discussion_question.data:
                q_discussion = Question(title=u'[Event discussion] %s' % form.title.data,
                                        author=request.user,
                                        text=u'This is the discussion for the event "%s"' % form.title.data,
                                        tags=form.tags.data)
            else:
                q_discussion = None

            #: Check for creating a question-object a discussion
            if form.info_question.data:
                q_info = Question(title=u'[Event information] %s' % form.title.data,
                                  author=request.user,
                                  text=u'This is the discussion for the event "%s"' % form.title.data,
                                  tags=form.tags.data)
            else:
                q_info = None

            db.session.commit()

            if q_discussion:
                q_discussion_id = q_discussion.id
            else:
                q_discussion_id = None

            if q_info:
                q_info_id = q_info.id
            else:
                q_info_id = None

            e = Event(title=form.title.data,
                      text=form.text.data,
                      author=request.user,
                      start_date=form.start.data,
                      end_date=form.end.data,
                      tags=form.tags.data,
                      discussion_question_id = q_discussion_id,
                      info_question_id = q_info_id)
            #if form.parent.data:
                #e.parent_id = form.parent.data
            db.session.commit()
            return redirect_to(e)

        return {
            'form': form,
        }

    @view('view')
    @templated('event/view.html', modifier=context_modifier)
    def view_event(self, request, id):
        e = Event.query.get(id)
        return {
            'event': e,
        }

    @view('oncoming')
    @templated('event/oncoming.html', modifier=context_modifier)
    def oncoming_events(self, request, year=None, month=None):
        events = Event.query.oncoming(validate_year(year),
                                      validate_month(month), 10000)
        return {
            'events': events,
        }

    @view('calendar')
    @templated('event/calendar.html', modifier=context_modifier)
    def calendar_events(self, request, year=None, month=None):
        year = validate_year(year)
        month = validate_month(month)

        day = date.today().day

        first_weekday_this_month = date(year, month, 1).weekday()

        if month == 1:
            pre = date(year - 1, 12, 1)
            post = date(year, 2, 1)
        elif month == 12:
            pre = date(year, 11, 1)
            post = date(year + 1, 1, 1)
        else:
            pre = date(year, month - 1, 1)
            post = date(year, month + 1, 1)

        days_in_premonth = calendar.monthrange(pre.year, pre.month)[1]

        days_in_month = calendar.monthrange(year, month)[1]

        #if month == 12:
        #    days_in_postmonth = calendar.monthrange(year - 1, 1)[1]
        #else:
        #    days_in_postmonth = calendar.monthrange(year, month + 1)[1]
        month_begin = date(year, month, 1)
        month_end = month_begin + timedelta(days_in_month)

        events = Event.query.during(month_begin, month_end)

        return {
            'events': events,
            'monthstart': first_weekday_this_month,
            'days_in_premonth': days_in_premonth,
            'days_in_month': days_in_month,
            'today': date.today(),
            'month_range': daterange(month_begin, month_end),
            'current': date(year, month, 1),
            'pre': pre,
            'post': post,
        }
