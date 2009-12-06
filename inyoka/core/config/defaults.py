# -*- coding: utf-8 -*-
"""
    inyoka.core.config.defaults
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements and documents the default values for our configuration.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
from os.path import join
from inyoka.core.config import BooleanField, TextField, IntegerField, DottedField
from inyoka.i18n import lazy_gettext


_default_media_data_path = join(os.environ['inyoka_contents'], 'media')


DEFAULTS = {
    # common config values
    'debug':                    BooleanField(default=False, help_text=lazy_gettext(
        u'Enable debug mode')),
    'media_root':               TextField(default=_default_media_data_path,
        help_text=lazy_gettext(u'The path to the media folder')),
    'cookie_secret':            TextField(default='CHANGEME',
                                          help_text=lazy_gettext(
        u'The secret used for hashing the cookies')),
    'base_domain_name':             TextField(default=u'inyoka.local:5000',
        help_text=lazy_gettext(u'Base domain name')),
    'cookie_domain_name':           TextField(default=u'.inyoka.local',
        help_text=lazy_gettext(u'Cookie domain name')),

    # database specific values
    'database.url':             TextField(default=u'sqlite:///dev.db',
                                          help_text=lazy_gettext(
        u'The database URL.  For more information about database settings '
        u'consult the Inyoka docs.')),
    'database.debug':           BooleanField(default=False, help_text=lazy_gettext(
        u'If enabled the database will collect the SQL statements and add them '
        u'to the bottom of the page for easier debugging.  Beside that the '
        u'sqlalchemy log is written to a `db.log` file.')),

    # template specific values
    'templates.path':            TextField(default='', help_text=lazy_gettext(
        u'Custom template path which is searched before the default path.')),

    # auth system specific values
    'auth.system':                  TextField(default=u'inyoka.portal.auth.EasyAuth',
        help_text=lazy_gettext(u'The Authsystem which should get used')),

    # routing specific config values
    # values are in the form of `subdomain:/submount`
    # if you only apply the submount use `/submount` the `:` will be completed
    'routing.urls.portal':          DottedField(default=u':/',
        help_text=lazy_gettext(u'Url mapping used for the portal application')),
    'routing.urls.calendar':        DottedField(default=u':/calendar',
        help_text=lazy_gettext(u'Url mapping used for the calendar application')),
    'routing.urls.news':            DottedField(default=u'news:/',
        help_text=lazy_gettext(u'Url mapping used for the news application')),
    'routing.urls.forum':           DottedField(default=u'forum:/',
        help_text=lazy_gettext(u'Url mapping used for the forum application')),
    'routing.urls.wiki':            DottedField(default=u'wiki:/',
        help_text=lazy_gettext(u'Url mapping used for the wiki application')),
    'routing.urls.paste':           DottedField(default=u'paste:/',
        help_text=lazy_gettext(u'Url mapping used for the paste application')),
    'routing.urls.planet':          DottedField(default=u'planet:/',
        help_text=lazy_gettext(u'Url mapping used for the planet application')),
    'routing.urls.testing':         DottedField(default=u':/testing',
        help_text=lazy_gettext(u'Url mapping used for the testing application')),

    # values for static and media serving
    'routing.urls.static':          DottedField(default=u':/_static',
        help_text=lazy_gettext(u'Url mapping used for static file serving')),
    'routing.urls.media':           DottedField(default=u':/_media',
        help_text=lazy_gettext(u'Url mapping used for media file serving')),
    'static_path':                  DottedField(default=u'static',
        help_text=lazy_gettext(u'Path to the directory for static files. '
                               u'Relative to the directory where '
                               u'the inyoka package lies in.')),
    'media_path':                   TextField(default=u'media',
        help_text=lazy_gettext(u'Path to the directory for shared static files, '
                               u'aka media. Relative to '
                               u'the directory where the inyoka package lies in.')),
}
