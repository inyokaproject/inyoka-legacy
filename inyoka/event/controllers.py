# -*- coding: utf-8 -*-
"""
    inyoka.event.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the event app.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import calendar
from datetime import datetime, date
from inyoka.core import exceptions as exc
from inyoka.core.api import IController, Rule, view, Response, \
    templated, db, redirect_to
from inyoka.utils.pagination import URLPagination
from inyoka.event.forms import AddEventForm
from inyoka.event.models import Event


def context_modifier(request, context):
    context.update(
        active='event'
    )


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
        form = AddEventForm(request.form)
        if form.validate_on_submit():
            # TODO request the form data
            e = Event(title=form.title.data,
                      text=form.text.data,
                      author=request.user,
                      start_date=form.start.data,
                      end_date=form.end.data)
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
        if not year or year < 1970:
            year = year or date.today().year
        if not month or month < 1 or month > 12:
            month = date.today().month
        events = Event.query.oncoming(year, month, 10000)
        return {
            'events': events,
        }

    @view('calendar')
    @templated('event/calendar.html', modifier=context_modifier)
    def calendar_events(self, request, year=None, month=None):
        if not year or year < 1970:
            year = year or date.today().year
        if not month or month < 1 or month > 12:
            month = date.today().month
        day = date.today().day
        events = Event.query.start_in(year, month)
        first_weekday_this_month = datetime(year, month, 1, 0, 0, 0).weekday()

        if month == 1:
            days_in_premonth = calendar.monthrange(year - 1, 12)[1]
        else:
            days_in_premonth = calendar.monthrange(year, month - 1)[1]

        days_in_month = calendar.monthrange(year, month)[1]

        #if month == 12:
        #    days_in_postmonth = calendar.monthrange(year - 1, 1)[1]
        #else:
        #    days_in_postmonth = calendar.monthrange(year, month + 1)[1]

        return {
            'events': events,
            'monthstart': first_weekday_this_month,
            'days_in_premonth': days_in_premonth,
            'days_in_month': days_in_month,
            'thisyear': year,
            'thismonth': month,
            'thisday': day,
            #'days_in_postmonth': days_in_postmonth,
        }

