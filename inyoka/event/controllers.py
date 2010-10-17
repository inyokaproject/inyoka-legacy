# -*- coding: utf-8 -*-
"""
    inyoka.event.controllers
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Controllers for the event app.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
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

    @view('calendar')
    @templated('event/calendar.html', modifier=context_modifier)
    def calendar_events(self, request, year=None, month=None):
        if not year or year < 1970:
            year = year or date.today().year
        if not month or month < 1 or month > 12:
            month = date.today().month
        events = Event.query.start_in(year, month)
        return {
            'events': events,
        }

