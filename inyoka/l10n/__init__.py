# -*- coding: utf-8 -*-
"""
    inyoka.l10n
    ~~~~~~~~~~~

    The localisation system for Inyoka.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
from functools import wraps
from datetime import date, datetime
import pytz
from babel import Locale, UnknownLocaleError
from babel import dates
from inyoka.i18n import get_locale
from inyoka.core.context import ctx


UTC = pytz.timezone('UTC')


def get_timezone(name=None):
    """Return the timezone for the given identifier or the timezone
    of the application based on the configuration.

    :param name: The identifier for the timezone.

    """
    if name is None:
        name = ctx.cfg['default_timezone']
    return pytz.timezone(name)


def rebase_to_timezone(datetime, force_utc=False):
    """Convert a datetime object to the users timezone.

    Note: Use this only for presentation never for calculations!

    :param datetime: The datetime object to convert.
    :param force_utc: Set to `True` if we have to force using UTC.
    """
    if datetime.tzinfo is None:
        datetime = datetime.replace(tzinfo=UTC)
    tzinfo = UTC if force_utc else get_timezone()
    return tzinfo.normalize(datetime.astimezone(tzinfo))


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

def get_dummy(func):
    @wraps(func)
    def _inner(*args, **kwargs):
        if 'locale' in kwargs and not kwargs['locale'] is dates.LC_TIME:
            kwargs['locale'] = get_locale()
        # yet only a few methods can work with timezone information properly
        if func.func_name in ('format_datetime', 'format_time'):
            kwargs['tzinfo'] = get_timezone(kwargs.get('tzinfo', None))
        return func(*args, **kwargs)
    return _inner

dict_ = globals()
for func in dates.__all__:
    dict_[func] = get_dummy(getattr(dates, func))
