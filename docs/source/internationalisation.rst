.. _internationalisation:

===========================
Internationalisation System
===========================

Inyoka comes with a builtin-system for localisation and internationalisation
commonly named as i18n and l10n.  Those systems can ease your life
with handling timezones and locales and help you with converting standardized
data to localized data.

i18n API
~~~~~~~~

.. automodule:: inyoka.i18n

.. autofunction:: gettext

.. autofunction:: ngettext

.. autofunction:: lazy_gettext

.. autofunction:: lazy_ngettext

.. autofunction:: list_languages

.. autofunction:: has_language

.. autofunction:: get_locale


l10n API
~~~~~~~~

.. automodule:: inyoka.l10n

.. autofunction:: get_timezone

.. autofunction:: rebase_to_timezone

.. autofunction:: to_datetime

.. autofunction:: format_month

.. autofunction:: humanize_number

.. autofunction:: timedeltaformat

.. todo: Add autodocs from wrapped babel functions
