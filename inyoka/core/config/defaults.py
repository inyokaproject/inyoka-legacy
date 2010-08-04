# -*- coding: utf-8 -*-
"""
    inyoka.core.config.defaults
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements and documents the default values for our configuration.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
from os.path import join
from inyoka.core.config import BooleanField, TextField, IntegerField,\
                               DottedField, ListField
from inyoka.i18n import lazy_gettext


_default_media_data_path = join(os.environ['INYOKA_MODULE'], 'media')
_default_templates_path = join(os.environ['INYOKA_MODULE'], 'templates')


DEFAULTS = {
    # common config values
    'debug':                        BooleanField(default=False,
        help_text=lazy_gettext(u'Enable debug mode')),
    'activated_components':         ListField(['inyoka.core.*',
        'inyoka.admin',
        'inyoka.portal',
        'inyoka.news',
        'inyoka.forum',
        'inyoka.paste',
        'inyoka.wiki'],
        lazy_gettext(u'List of activated components')),
    'deactivated_components':       ListField(['inyoka.core.tasks'],
        lazy_gettext(u'List of deactivted components')),
    'media_root':                   TextField(default=_default_media_data_path,
        help_text=lazy_gettext(u'The path to the media folder')),
    'secret_key':                TextField(default=u'CHANGEME',
        help_text=lazy_gettext(u'The secret used for hashing the cookies and '
                               u'other security salting')),
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
    'anonymous_name':               TextField(default=u'anonymous',
        help_text=lazy_gettext(u'The name of the anonymous user.')),
    'enable_csrf_checks':           BooleanField(default=True,
        help_text=lazy_gettext(u'Enable or disable CSRF Protection.')),
    'recaptcha.use_ssl':            BooleanField(default=True,
        help_text=lazy_gettext(u'Use SSL for ReCaptcha requests, defaults to True')),
    'recaptcha.public_key':         TextField(
        default=u'6Lc1LwsAAAAAAPSQ4FcfLKJVcwzicnZl8v-RmeLj',
        help_text=lazy_gettext(u'Recaptcha public key')),
    'recaptcha.private_key':        TextField(
        default=u'6Lc1LwsAAAAAAAKaGUBaEpTOfXKDWe6QjIlmMM9b',
        help_text=lazy_gettext(u'Recaptcha private key')),
    'website_title':                 TextField(default=u'Inyoka Portal',
        help_text=lazy_gettext(u'The website title to show in various places')),
    'mail_address':                  TextField(default=u'system@inyoka.local',
        help_text=lazy_gettext(u'The mail address used for sending mails')),
    'permanent_session_lifetime':    IntegerField(default=30,
        help_text=lazy_gettext(u'The duration a permanent session is valid. '
                               u'Defined in days, defaults to 30.')),

    # database specific values
    'database.url':                 TextField(default=u'sqlite:///dev.db',
        help_text=lazy_gettext(u'The database URL.  For more information '
            u'about database settings consult the Inyoka docs.')),
    'database.debug':               BooleanField(default=False,
        help_text=lazy_gettext(u'If enabled the database will collect '
            u'the SQL statements and add them to the bottom of the page '
            u'for easier debugging.')),
    'database.echo':                BooleanField(default=False,
        help_text=lazy_gettext(u'If enabled the database will echo '
            u'all submitted statements to the default logger.  That defaults '
            u'to stdout.')),
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
    'imaging.thumbnailsize':            TextField(default=u'100x100',
        help_text=lazy_gettext(u'Portal thumbnail size.')),

    # template specific values
    'templates.path':               TextField(default=_default_templates_path,
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

    #TODO: yet a hack untill we have proper information about what an app is
    'templates.packages.portal':    TextField(default=u'inyoka.portal'),
    'templates.packages.news':    TextField(default=u'inyoka.news'),
    'templates.packages.forum':    TextField(default=u'inyoka.forum'),
    'templates.packages.wiki':    TextField(default=u'inyoka.wiki'),
    'templates.packages.paste':    TextField(default=u'inyoka.paste'),
    'templates.packages.planet':    TextField(default=u'inyoka.planet'),

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
    'routing.urls.usercp':          DottedField(default=u':/usercp',
        help_text=lazy_gettext(u'Url mapping used for the usercp application')),
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
    'routing.urls.admin':           DottedField(default=u'admin:/',
        help_text=lazy_gettext(u'Url mapping used for the admin application')),
    'routing.urls.api':           DottedField(default=u'api:/',
        help_text=lazy_gettext(u'Url mapping used for the API')),

    # Do never change that value!!!!
    'routing.urls.test':             DottedField(default=u'_test_:/',
        help_text=lazy_gettext(u'Url mapping used for the testing system.  '
                               u'Do never chage that value!')),

    # values for static and media serving
    'routing.urls.static':          DottedField(default=u'static:/',
        help_text=lazy_gettext(u'Url mapping used for static file serving')),
    'routing.urls.media':           DottedField(default=u'media:/',
        help_text=lazy_gettext(u'Url mapping used for media file serving')),
    'static_path':                  TextField(default=u'static',
        help_text=lazy_gettext(u'Path to the directory for static files. '
                               u'Relative to the directory where '
                               u'the inyoka package lies in.')),
    'media_path':                   TextField(default=u'media',
        help_text=lazy_gettext(u'Path to the directory for shared static files, '
                               u'aka media. Relative to '
                               u'the directory where the inyoka package lies in.')),

    # wiki specific values
    'wiki.index.name':              TextField(default=u'Main Page',
        help_text=lazy_gettext(u'Name of the wiki index page (the one a user '
                               u"accessing the wiki's / is redirected to)")),

    # various paste settings
    'paste.diffviewer_syntax_highlighting_threshold': IntegerField(default=0,
        help_text=lazy_gettext(u'Files with lines greater than this number '
                               u'will not have syntax highlighting. '
                               u'Enter 0 for no limit.')),

    # celery settings
    'celery.result_backend':        TextField(u'amqp',''),
    'celery.imports':               ListField(['inyoka.core.tasks'],''),

    # ampq broker settings
    'broker.host':                  TextField(u'localhost', ''),
    'broker.port':                  IntegerField(5672, ''),
    'broker.user':                  TextField(u'inyoka', ''),
    'broker.password':              TextField(u'default', ''),
    'broker.vhost':                 TextField(u'inyoka', ''),
}
