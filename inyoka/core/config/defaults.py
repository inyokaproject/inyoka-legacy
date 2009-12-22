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


_default_media_data_path = join(os.environ['INYOKA_MODULE'], 'media')


DEFAULTS = {
    # common config values
    'debug':                        BooleanField(default=False,
        help_text=lazy_gettext(u'Enable debug mode')),
    'media_root':                   TextField(default=_default_media_data_path,
        help_text=lazy_gettext(u'The path to the media folder')),
    'cookie_secret':                TextField(default=u'CHANGEME',
        help_text=lazy_gettext(u'The secret used for hashing the cookies')),
    'base_domain_name':             TextField(default=u'inyoka.local:5000',
        help_text=lazy_gettext(u'Base domain name')),
    'cookie_domain_name':           TextField(default=u'.inyoka.local',
        help_text=lazy_gettext(u'Cookie domain name')),
    'cookie_name':                  TextField(default=u'inyoka-session',
        help_text=lazy_gettext(u'Cookie name')),
    'language':                     TextField(default=u'en',
        help_text=lazy_gettext(u'The current language locale')),
    'default_timezone':             TextField(default=u'Europe/Berlin',
        help_text=lazy_gettext(u'The default timezone for all users.')),

    # database specific values
    'database.url':                 TextField(default=u'sqlite:///dev.db',
        help_text=lazy_gettext(u'The database URL.  For more information '
            u'about database settings consult the Inyoka docs.')),
    'database.debug':               BooleanField(default=False,
        help_text=lazy_gettext(u'If enabled the database will collect '
            u'the SQL statements and add them to the bottom of the page '
            u'for easier debugging.  Beside that the sqlalchemy log is '
            u'written to a `db.log` file.')),
    'database.pool_recycle':        IntegerField(default=-1, min_value=-1,
        help_text=lazy_gettext(u'If set to non -1, number of seconds between '
            u'connection recycling. If this timeout is surpassed the '
            u'connection will be closed and replaced with a newly opened connection.')),
    'database.pool_timeout':        IntegerField(default=30, min_value=5,
        help_text=lazy_gettext(u'The number of seconds to wait before giving '
            u'up on returning a connection.  This will not be used if the used'
            u' database is one of SQLite, Access or Informix as those don\'t '
            u'support queued connection pools.')),

    # imaging specific values
    'imaging.backend':              TextField(default=u'pil',
        help_text=lazy_gettext(u'Imaging backend to use.')),
    'imaging.avatarsize':           TextField(default=u'50x50',
        help_text=lazy_gettext(u'Portal avatar size.')),
    'imaging.thumbnail':            TextField(default=u'100x100',
        help_text=lazy_gettext(u'Portal thumbnail size.')),

    # template specific values
    'templates.path':               TextField(default=u'',
        help_text=lazy_gettext(u'Custom template path which is '
            u'searched before the default path.')),
    'templates.auto_reload':        BooleanField(default=True,
        help_text=lazy_gettext(u'Auto reload template files if they changed '
                               u'their contents.')),
    'templates.use_cache':          BooleanField(default=False,
        help_text=lazy_gettext(u'Use either memory, filesystem or memcached '
                               u'bytecode caches')),
    'templates.use_memcached_cache':      BooleanField(default=False,
        help_text=lazy_gettext(u'Use Memcached for bytecode caching')),
    'templates.use_filesystem_cache':     BooleanField(default=False,
        help_text=lazy_gettext(u'Use filesystem for bytecode caching')),

    # caching
    'caching.system':               TextField(default=u'null',
        help_text=lazy_gettext(u'Choose one of null, simple, memcached or filesystem '
            u'for the caching system.')),
    'caching.filesystem_cache_path': TextField(default=u'/tmp/_inyoka_cache',
        help_text=lazy_gettext(u'The path for the filesystem caches')),
    'caching.timeout':              IntegerField(default=300, min_value=10,
        help_text=lazy_gettext(u'The timeout for the caching system')),
    'caching.memcached_servers':    TextField(default=u'',
        help_text=lazy_gettext(u'Comma seperated list of memcached servers')),

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
