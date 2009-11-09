# -*- coding: utf-8 -*-
"""
    inyoka.core.config.defaults
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements and documents the default values for our configuration.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.i18n import lazy_gettext
from inyoka.core.environ import MEDIA_DATA
from inyoka.core.config import BooleanField, TextField, IntegerField


DEFAULTS = {
    'debug':                    BooleanField(default=False, help_text=lazy_gettext(
        u'Enable debug mode')),
    'media_root':               TextField(default=MEDIA_DATA, help_text=lazy_gettext(
        u'The path to the media folder')),
    'template_path':            TextField(default='', help_text=lazy_gettext(
        u'Custom template path which is searched before the default path.')),
    'cookie_secret':            TextField(default='CHANGEME',
                                          help_text=lazy_gettext(
        u'The secret used for hashing the cookies')),
    'database_url':             TextField(default=u'sqlite:///dev.db',
                                          help_text=lazy_gettext(
        u'The database URL.  For more information about database settings '
        u'consult the Inyoka docs.')),
    'database_debug':           BooleanField(default=False, help_text=lazy_gettext(
        u'If enabled the database will collect the SQL statements and add them '
        u'to the bottom of the page for easier debugging.  Beside that the '
        u'sqlalchemy log is written to a `db.log` file.')),
    'auth_system':                  TextField(default=u'inyoka.portal.auth.EasyAuth',
        help_text=lazy_gettext(u'The Authsystem which should get used')),
    'routing.portal.subdomain':     TextField(default=u'',
        help_text=lazy_gettext(u'Subdomain used for the portal application')),
    'routing.portal.submount':      TextField(default=u'/',
        help_text=lazy_gettext(u'Submount used for the portal application')),
    'routing.calendar.subdomain':   TextField(default=u'',
        help_text=lazy_gettext(u'Subdomain used for the calendar application')),
    'routing.calendar.submount':    TextField(default=u'/calendar',
        help_text=lazy_gettext(u'Submount used for the calendar application')),
    'routing.news.subdomain':       TextField(default=u'news',
        help_text=lazy_gettext(u'Subdomain used for the news application')),
    'routing.news.submount':        TextField(default=u'/',
        help_text=lazy_gettext(u'Submount used for the news application')),
    'routing.forum.subdomain':     TextField(default=u'forum',
        help_text=lazy_gettext(u'Subdomain used for the forum application')),
    'routing.forum.submount':      TextField(default=u'/',
        help_text=lazy_gettext(u'Submount used for the forum application')),
    'routing.wiki.subdomain':     TextField(default=u'wiki',
        help_text=lazy_gettext(u'Subdomain used for the wiki application')),
    'routing.wiki.submount':      TextField(default=u'/',
        help_text=lazy_gettext(u'Submount used for the wiki application')),
    'routing.paste.subdomain':     TextField(default=u'paste',
        help_text=lazy_gettext(u'Subdomain used for the paste application')),
    'routing.paste.submount':      TextField(default=u'/',
        help_text=lazy_gettext(u'Submount used for the paste application')),
    'routing.planet.subdomain':     TextField(default=u'planet',
        help_text=lazy_gettext(u'Subdomain used for the forum application')),
    'routing.planet.submount':      TextField(default=u'/',
        help_text=lazy_gettext(u'Submount used for the planet application')),
    'routing.testing.subdomain':    TextField(default=u'',
        help_text=lazy_gettext(u'Subdomain used for the testing application')),
    'routing.testing.submount':    TextField(default=u'/testing',
        help_text=lazy_gettext(u'Submount used for the testing application')),
    'base_domain_name':             TextField(default=u'inyoka.local:5000',
        help_text=lazy_gettext(u'Base domain name')),
    'cookie_domain_name':           TextField(default=u'.inyoka.local',
        help_text=lazy_gettext(u'Cookie domain name')),
    'static_path':                  TextField(default=u'static',
        help_text=lazy_gettext(u'Path to the directory for static files. Relative to the directory where '
                               u'the inyoka package lies in.')),
    'media_path':                  TextField(default=u'media',
        help_text=lazy_gettext(u'Path to the directory for shared static files, aka media. Relative to '
                               u'the directory where the inyoka package lies in.')),

}
