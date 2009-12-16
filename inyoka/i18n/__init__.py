# -*- coding: utf-8 -*-
"""
    inyoka.i18n
    ~~~~~~~~~~~

    The internationalisation system for Inyoka.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
from os.path import realpath, dirname
from gettext import NullTranslations
from babel import Locale, UnknownLocaleError
from babel.support import Translations as TranslationsBase, LazyProxy
from inyoka.core.context import config


__all__ = ['_', 'gettext', 'ngettext', 'lazy_gettext', 'lazy_ngettext']



_translations = None


def load_core_translations(locale):
    """Return the matching locale catalog for `locale`"""
    global _translations
    base = realpath(dirname(__file__))
    ret = _translations = Translations.load(base, locale)
    return ret


def get_translations():
    """Return the translations required for translating.

    Note that this function only returns cached values but neither
    regenerates already cached values.  For that purpose use
    :func:`load_core_translations`
    """
    global _translations
    if _translations is None:
        _translations = load_core_translations(config['language'])
    return _translations


def get_locale(locale=None):
    """Return a :cls:`Locale` instance for `locale` or the current
    configured locale if none is given.
    """
    if locale is None:
        locale = config['language']
    locale = Locale.parse(locale)
    return locale


class Translations(TranslationsBase):

    @classmethod
    def load(cls, path, locale=None, domain='messages',
             gettext_lookup=False):
        """Load the translations from the given path."""
        locale = get_locale(locale)
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
    args = [path, str(get_locale(locale)), domain + '.mo']
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

_ = gettext
