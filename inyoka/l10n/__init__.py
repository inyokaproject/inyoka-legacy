# -*- coding: utf-8 -*-
"""
    inyoka.l10n
    ~~~~~~~~~~~

    The localisation system for Inyoka.  This module is mostly more a wrapper
    around various babel functions than a complete l10n system.

    All formatting and parsing methods are automatically wrapped to use our
    :func:`~inyoka.l10n.get_timezone` and :func:`~inyoka.i18n.get_locale`
    functions to be aware of locales and timezones.

    Please note that all functions here always return a localized object so
    do not use those for calculations only for presentation purposes!

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from __future__ import division
import re
from functools import wraps
from datetime import date, datetime, timedelta
import pytz
from babel import dates
from babel.dates import TIMEDELTA_UNITS

from inyoka.i18n import get_locale, lazy_gettext, _
from inyoka.context import ctx


timestamp_regexp = re.compile(r'''
    ^(?P<year>[0-9][0-9][0-9][0-9])
    -(?P<month>[0-9][0-9]?)
    -(?P<day>[0-9][0-9]?)
    (?:(?:[Tt]|[ \t]+)
    (?P<hour>[0-9][0-9]?)
    :(?P<minute>[0-9][0-9])
    :(?P<second>[0-9][0-9])
    (?:\.(?P<fraction>[0-9]*))?
    (?:[ \t]*(?P<tz>Z|(?P<tz_sign>[-+])(?P<tz_hour>[0-9][0-9]?)
    (?::(?P<tz_minute>[0-9][0-9]))?))?)?$''', re.X)


timeonly_regexp = re.compile(
        r'''^(?P<hour>[0-9][0-9]?)
            :(?P<minute>[0-9][0-9])
            (?::(?P<second>[0-9][0-9]))?
            (?:\.(?P<fraction>[0-9]*))?$''', re.X)


UTC = pytz.timezone('UTC')


def get_timezone(name=None):
    """Return the timezone for the given identifier or the timezone
    of the application based on the configuration.

    :param name: The identifier for the timezone.

    """
    if name is None:
        name = ctx.cfg['default_timezone']
    return pytz.timezone(name)


def rebase_to_timezone(dtobj, force_utc=False):
    """Convert a datetime object to the users timezone.

    Note: Use this only for presentation never for calculations!

    :param datetime: The datetime object to convert.
    :param force_utc: Set to `True` if we have to force using UTC.
    """
    if dtobj.tzinfo is None:
        dtobj = dtobj.replace(tzinfo=UTC)
    tzinfo = UTC if force_utc else get_timezone()
    return tzinfo.normalize(dtobj.astimezone(tzinfo))


def to_datetime(obj):
    """Convert `obj` into a `datetime` object.

    * If `obj` is a `datetime` object it is returned untouched.
    * if `obj` is None the current time in UTC is used.
    * if `obj` is a `date` object it will be converted into a `datetime` object.
    * if `obj` is a number it is interpreted as a timestamp.

    Note: All values are localized to the users timezone.
          Never use this for calculations, only for presentation!
    """
    if obj is None:
        dt = datetime.utcnow()
    elif isinstance(obj, datetime):
        dt = obj
    elif isinstance(obj, date):
        dt = datetime(obj.year, obj.month, obj.day)
    elif isinstance(obj, (int, long, float)):
        dt = datetime.fromtimestamp(obj)
    else:
        raise TypeError('expecting datetime, date int, long, float, or None; '
                        'got %s' % type(obj))
    return rebase_to_timezone(dt)


# Wrap all api functions from Babel <http://babel.edgewall.org> with
# support for our i18n hacked in for easier usage.
#
# For detailed documentation see Babel online docs:
# http://babel.edgewall.org/wiki/ApiDocs/0.9/babel.dates

_timezone_aware = ('format_datetime', 'format_time')


def get_dummy(func):
    #: avoid failing doctest from the original docstring
    if func.func_name in _timezone_aware:
        w = wraps(func, ('__module__', '__name__'))
    else:
        w = wraps(func, ('__module__', '__name__', '__doc__'))

    @w
    def _inner(*args, **kwargs):
        if 'locale' not in kwargs or kwargs['locale'] is dates.LC_TIME:
            kwargs['locale'] = get_locale()
        # yet only a few methods can work with timezone information properly
        # we also check if the applied value is a basestring.  If it is
        # we convert it to a proper pytz timezone value.  If it's not we
        # assume to get a proper timezone value.
        tzinfo = kwargs.get('tzinfo', None)
        if isinstance(tzinfo, basestring) or tzinfo is None:
            tzinfo = get_timezone(tzinfo)
        if func.func_name in _timezone_aware:
            kwargs['tzinfo'] = tzinfo

        return func(*args, **kwargs)
    return _inner

dict_ = globals()
_additional_all = ['get_month_names', 'get_day_names', 'get_era_names',
    'get_period_names', 'get_quarter_names']
for func in dates.__all__ + _additional_all:
    dict_[func] = get_dummy(getattr(dates, func))


def format_month(date=None):
    """Format month and year of a date."""
    return dates.format_date(date, 'MMMM YYYY')


def humanize_number(number):
    """Format numbers from 0 to 12 to strings.
    unfortunately, this cannot be done with Babel.

    Usage Example::

        >>> humanize_number(6)
        u'six'
        >>> humanize_number(13)
        u'13'
        >>> humanize_number(u'some_string')
        u'some_string'

    """
    strings = [_(u'zero'), _(u'one'), _(u'two'), _(u'three'), _(u'four'),
               _(u'five'), _(u'six'), _(u'seven'), _(u'eight'),
               _(u'nine'), _(u'ten'), _(u'eleven'), _(u'twelve')
              ]
    return strings[number] if number in xrange(13) else unicode(number)


def _format_timedelta(delta, granularity='second', threshold=.85, locale=None):
    """Return a time delta according to the rules of the given locale.

    function copied and slightly modified from babel.dates.format_timedelta
    see babel package information for details and
    http://babel.edgewall.org/wiki/License for the license

    """
    if isinstance(delta, timedelta):
        seconds = int((delta.days * 86400) + delta.seconds)
    else:
        seconds = delta

    if locale is None:
        locale = get_locale()

    for unit, secs_per_unit in TIMEDELTA_UNITS:
        value = abs(seconds) / secs_per_unit
        if value >= threshold or unit == granularity:
            if unit == granularity and value > 0:
                value = max(1, value)
            value = int(round(value))
            plural_form = locale.plural_form(value)
            pattern = locale._data['unit_patterns'][unit][plural_form]
            return pattern.replace(u'{0}', humanize_number(value))

    return u''


# our locale aware special format methods
def timedeltaformat(datetime_or_timedelta, threshold=.85, granularity='second'):
    """Special locale aware timedelta format function

    Usage Example::

        >>> timedeltaformat(timedelta(weeks=12))
        u'three mths ago'
        >>> timedeltaformat(timedelta(seconds=30))
        u'30 secs ago'
        >>> timedeltaformat(timedelta(seconds=0))
        u'just now'

        The granularity parameter can be provided to alter the lowest unit
        presented, which defaults to a second.

        >>> timedeltaformat(timedelta(hours=3), granularity='day')
        u'one day ago'

        The threshold parameter can be used to determine at which value the
        presentation switches to the next higher unit. A higher threshold factor
        means the presentation will switch later. For example:

        >>> timedeltaformat(timedelta(hours=23), threshold=0.9)
        u'one day ago'
        >>> timedeltaformat(timedelta(hours=23), threshold=1.1)
        u'23 hrs ago'

    :param datetime_or_timedelta: Either a datetime or timedelta object.
                                  If it's a datetime object we caclculate the
                                  timedelta from this object to now (using UTC)
    :param threshold: factor that determines at which point the presentation
                      switches to the next higher unit
    :param granularity: determines the smallest unit that should be displayed,
                        the value can be one of "year", "month", "week", "day",
                        "hour", "minute" or "second"

    """
    if isinstance(datetime_or_timedelta, datetime):
        datetime_or_timedelta = datetime.utcnow() - datetime_or_timedelta

    if datetime_or_timedelta <= timedelta(seconds=3):
        return _(u'just now')

    timedelta_ = _format_timedelta(datetime_or_timedelta, granularity,
                                  threshold=threshold)
    return lazy_gettext(u'%(timedelta)s ago') % {'timedelta': timedelta_}


def parse_timestamp(value):
    """Try to simply parse a timestamp value into a datetime object.

    .. note::

        Do never rely on that function for presentation or calculation
        purposes.  It's more or less only used for test serializaion.
    """
    match = timestamp_regexp.match(value)
    if match is None:
        raise ValueError('Unknown DateTime format, %s try %%Y-%%m-%%d %%h:%%m:%%s.d' % value)

    values = match.groupdict()
    year = int(values['year'])
    month = int(values['month'])
    day = int(values['day'])
    if not values['hour']:
        return date(year, month, day)

    hour = int(values['hour'])
    minute = int(values['minute'])
    second = int(values['second'])
    fraction = 0
    if values['fraction']:
        fraction = values['fraction'][:6]
        while len(fraction) < 6:
            fraction += '0'
        fraction = int(fraction)
    delta = None
    if values['tz_sign']:
        tz_hour = int(values['tz_hour'])
        tz_minute = int(values['tz_minute'] or 0)
        delta = timedelta(hours=tz_hour, minutes=tz_minute)
        if values['tz_sign'] == '-':
            delta = -delta
    data = datetime(year, month, day, hour, minute, second, fraction)
    if delta:
        data -= delta
    return data


def parse_timeonly(value):
    match = timeonly_regexp.match(value)
    if match is None:
        raise ValueError('Unknown Time format, %s try HH:MM:SS.dddddd' % value)

    values = match.groupdict()
    hour = int(values['hour'])
    minute = int(values['minute'])
    second = 0
    if values['second']:
        second = int(values['second'])
    fraction = 0
    if values['fraction']:
        fraction = values['fraction'][:6]
        while len(fraction) < 6:
            fraction += '0'
        fraction = int(fraction)
    return datetime.time(hour, minute, second, fraction)
