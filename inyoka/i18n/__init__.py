# -*- coding: utf-8 -*-
"""
    inyoka.i18n
    ~~~~~~~~~~~

    The internationalisation system for Inyoka.  This is used to
    implement features like translating Inyoka and such things.

    Use the :func:`_` and :func:`lazy_gettext` functions for easy
    marking strings as translatable.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import re
import json
from os.path import realpath, dirname
from gettext import NullTranslations
from weakref import WeakKeyDictionary
from babel import Locale, UnknownLocaleError
from babel.support import Translations as TranslationsBase, LazyProxy
from inyoka.context import ctx
from inyoka.signals import signals
from inyoka.core.config import TextConfigField


__all__ = ['_', 'gettext', 'ngettext', 'lazy_gettext', 'lazy_ngettext']


_translations = None
_js_translations = WeakKeyDictionary()
translations_reloaded = signals.signal('translations-reloaded')


language = TextConfigField('language', u'en')


def load_core_translations(locale):
    """Return the matching locale catalog for `locale`"""
    global _translations
    base = realpath(dirname(__file__))
    ret = _translations = Translations.load(base, locale)
    return ret


@ctx.cfg.reload_signal.connect
def reload_translations(sender, config):
    global _translations
    load_core_translations(config['language'])
    translations_reloaded.send('translations-reloaded')


def get_translations():
    """Return the translations required for translating.

    Note that this function only returns cached values but neither
    regenerates already cached values.  For that purpose use
    :func:`load_core_translations`
    """
    global _translations
    if _translations is None:
        _translations = load_core_translations(ctx.cfg['language'])
    return _translations


def get_locale(locale=None):
    """Return a :class:`Locale` instance for `locale` or the current
    configured locale if none is given.
    """
    if locale is None:
        locale = ctx.cfg['language']
    locale = Locale.parse(locale)
    return locale


class Translations(TranslationsBase):
    """Our translations implementation to hook in our
    own catalog finding algorithm.  We do not use a
    GNU Gettext compatible folder structure.
    """

    @classmethod
    def load(cls, path, locale=None, domain='messages',
             gettext_lookup=False):
        """Load the translations from the given path."""
        locale = get_locale(locale)
        catalog = find_catalog(path, domain, locale, gettext_lookup)
        if catalog:
            return Translations(fileobj=open(catalog))
        return NullTranslations()

    def __repr__(self):
        return '<%s: "%s">' % (type(self).__name__, get_locale())

    # Always use the unicode versions, we don't support byte strings
    gettext = TranslationsBase.ugettext
    ngettext = TranslationsBase.ungettext


def find_catalog(path, domain, locale, gettext_lookup=False):
    """Finds the catalog for the given locale on the path.  Return the
    filename of the .mo file if found, otherwise `None` is returned.
    """
    args = [path, str(get_locale(locale)), domain + '.mo']
    if gettext_lookup:
        args.insert(-1, 'LC_MESSAGES')
    catalog = os.path.join(*args)
    if os.path.isfile(catalog):
        return catalog


def lazy_gettext(string):
    """A lazy version of :func:`gettext`."""
    return LazyProxy(gettext, string)


def lazy_ngettext(singular, plural, n):
    """A lazy version of :func:`ngettext`."""
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


def pluralexpr(forms):
    match = re.search(r'\bplural\s*=\s*([^;]+)', forms)
    if not match:
        raise ValueError('Failed to parse plural_forms %r' % (forms,))
    return match.group(1)


def serve_javascript(request):
    """Serves the JavaScript translations."""
    from inyoka.core.http import Response

    code = _js_translations.get(ctx.dispatcher)
    if code is None:
        messages = {}
        translations = get_translations()
        catalog = translations._catalog if hasattr(translations, '_catalog') else {}
        data = {'domain': 'messages', 'locale': unicode(get_locale())}

        for msgid, msgstr in catalog.iteritems():
            if isinstance(msgid, (list, tuple)):
                messages.setdefault(msgid[0], {})
                messages[msgid[0]][msgid[1]] = msgstr
            elif msgid:
                messages[msgid] = msgstr
            else:
                for line in msgstr.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if ':' not in line:
                        continue
                    name, val = line.split(':', 1)
                    name = name.strip().lower()
                    if name == 'plural-forms':
                        data['plural_expr'] = pluralexpr(val)
                        break

        data['messages'] = messages

        code = u''.join((
            ('// Generated messages javascript file from compiled MO file\n'),
            ('babel.Translations.load('),
            (json.dumps(data)),
            (').install();\n')
        ))
        _js_translations[ctx.dispatcher] = code

    response = Response(code, mimetype='application/javascript')
    response.add_etag()
    response.make_conditional(request)
    return response

#: synonym for :func:`gettext`
_ = gettext
