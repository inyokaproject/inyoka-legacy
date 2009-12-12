# -*- coding: utf-8 -*-
"""
    inyoka.i18n
    ~~~~~~~~~~~

    The internationalisation system for Inyoka.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import pytz
from os.path import realpath, dirname
from gettext import NullTranslations
from babel import Locale, UnknownLocaleError
from babel.support import Translations as TranslationsBase, LazyProxy
from babel.dates import format_date, format_datetime, format_time
from inyoka.core.context import config


__all__ = ['_', 'gettext', 'ngettext', 'lazy_gettext', 'lazy_ngettext']


UTC = pytz.timezone('UTC')

_translations = None

def load_core_translations(locale):
    """Return the matching locale catalog for `locale`"""
    global _translations
    base = realpath(dirname(__file__))
    ret = _translations = Translations.load(base, locale)
    return ret


def get_translations():
    global _translations
    if _translations is None:
        _translations = load_core_translations(config['language'])
    return _translations


class Translations(TranslationsBase):

    @classmethod
    def load(cls, path, locale=None, domain='messages',
             gettext_lookup=False):
        """Load the translations from the given path."""
        locale = Locale.parse(locale)
        catalog = find_catalog(path, domain, locale, gettext_lookup)
        if catalog:
            return Translations(fileobj=open(catalog))
        return NullTranslations()

    # Always use the unicode versions, we don't support byte strings
    gettext = TranslationsBase.ugettext
    ngettext = TranslationsBase.ungettext


def find_catalog(path, domain, locale, gettext_lookup=False):
    """Finds the catalog for the given locale on the path.  Return sthe
    filename of the .mo file if found, otherwise `None` is returned.
    """
    args = [path, str(Locale.parse(locale)), domain + '.mo']
    if gettext_lookup:
        args.insert(-1, 'LC_MESSAGES')
    catalog = os.path.join(*args)
    if os.path.isfile(catalog):
        return catalog


def lazy_gettext(string):
    """A lazy version of `gettext`."""
    return LazyProxy(gettext, string)


def lazy_ngettext(singular, plural, n):
    """A lazy version of `ngettext`."""
    return LazyProxy(ngettext, singular, plural, n)


def gettext(string):
    """Translate the given string to the language of the application."""
    return unicode(get_translations().ugettext(string))


def ngettext(singular, plural, n):
    """Translate the possible pluralized string to the language of the
    application.
    """
    if get_locale() is None:
        if n == 1:
            return singular
        return plural
    return unicode(get_translations().ungettext((singular, plural, n)))


def get_timezone(name=None):
    """Return the timezone for the given identifier or the timezone
    of the application based on the configuration.
    """
    if name is None:
        return UTC
    return pytz.timezone(name)


def list_languages():
    """Return a list of all languages."""
    languages = [('en', Locale('en').display_name)]
    folder = os.path.dirname(__file__)

    for filename in os.listdir(folder):
        if filename == 'en' or not \
           os.path.isdir(os.path.join(folder, filename)):
            continue
        try:
            l = Locale.parse(filename)
        except UnknownLocaleError:
            continue
        languages.append((str(l), l.display_name))

    languages.sort(key=lambda x: x[1].lower())
    return languages


def has_language(language):
    """Check if a language exists."""
    return language in dict(list_languages())


def rebase_to_timezone(datetime):
    """Convert a datetime object to the blog timezone."""
    if datetime.tzinfo is None:
        datetime = datetime.replace(tzinfo=UTC)
    tzinfo = get_timezone()
    return tzinfo.normalize(datetime.astimezone(tzinfo))


_ = gettext
