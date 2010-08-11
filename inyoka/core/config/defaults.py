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


#: Enable debug mode
debug = BooleanField('debug', default=False)

#: List of activasted components
activated_components = ListField('activated_components', [
    'inyoka.core.*',
    'inyoka.admin',
    'inyoka.portal',
    'inyoka.news.api',
    'inyoka.forum.api',
    'inyoka.paste.api',
    'inyoka.wiki.api'])

#: List of deactivated components
deactivated_components = ListField('deactivated_components', ['inyoka.core.tasks'])

#: The path to the media folder
media_root = TextField('media_root', default=_default_templates_path)

#: The secret key used for hashing the cookies and other
#: security salting.
secret_key = TextField('secret_key', default=u'CHANGEME')

#: Base domain name
base_domain_name = TextField('base_domain_name', default=u'inyoka.local:5000')

#: Cookie domain name
cookie_domain_name = TextField('cookie_domain_name', default=u'.inyoka.local')

#: Cookie name
cookie_name = TextField('cookie_name', default=u'inyoka-session')

#: The current language locale
language = TextField('language', default=u'en')

#: The default timezone for all users
default_timezone = TextField('default_timezone', default=u'Europe/Berlin')

#: THe name of the anonymous user
anonymous_name = TextField('anonymous_name', default=u'anonymous')

#: Enable or disable CSRF Protection
enable_csrf_checks = BooleanField('enable_csrf_checks', default=True)

#: The website title to show in various places
website_title = TextField('website_title', default=u'Inyoka Portal')

#: The mail address used for sending mails
mail_address = TextField('mail_address', default=u'system@inyoka.local')

#: The duration a permanent session is valid.  Defined in days, defaults to 30
permanent_session_lifetime = IntegerField('permanent_session_life', default=30)

#: Use SSL for ReCaptcha requests, defaults to True
recaptcha_use_ssl = BooleanField('recaptcha.use_ssl', default=True)

#: ReCaptcha public key
recaptcha_public_key = TextField('recaptcha.public_key',
    default=u'6Lc1LwsAAAAAAPSQ4FcfLKJVcwzicnZl8v-RmeLj')

#: ReCaptcha private key
recaptcha_private_key = TextField('recaptcha.private_key',
    default=u'6Lc1LwsAAAAAAAKaGUBaEpTOfXKDWe6QjIlmMM9b')

#: The database URL.  For more information about database settings
#: consult the Inyoka docs.
database_url = TextField('database.url', default=u'sqlite:///dev.db')

#: Set database debug.  If enabled the database will collect the SQL
#: statements and add them to the bottom of the page for easier debugging.
database_debug = BooleanField('database.debug', default=False)

#: Set database echo.  If enabled the database will echo all submitted
#: statements to the default logger.  That defaults to stdout.
database_echo = BooleanField('database.echo', default=False)

#: Set database pool recycle.  If set to non -1, used as number of seconds
#: between connection recycling.  If this timeout is surpassed, the connection
#: will be closed and replaced with a newly opened connection.
database_pool_recycle = IntegerField('database.pool_recycle', default=-1, min_value=-1)

#: Set database pool timeout.  The number of seconds to wait before giving
#: up on a returning connection.  This will not be used if the used database
#: is one of SQLite, Access or Informix as those don't support
#: queued connection pools.
database_pool_timeout = IntegerField('database.pool_timeout', default=30, min_value=5)


#: Set imaging backend to use.
imaging_backend = TextField('imaging.backend', default=u'pil')

#: Portal avatar size.
imaging_avatarsize = TextField('imaging.avatarsize', default=u'50x50')

#: Portal thumbnail size.
imaging_thumbnailsize = TextField('imaging.thumbnailsize', default=u'100x100')

#: Custom template path which is searched before the default path
templates_path = TextField('templates.path', default=_default_templates_path)

#: Auto reload template files if they changed
templates_auto_reload = BooleanField('templates.auto_reload', default=True)

#: Use either ’memory’, ’filesystem’, or ’memcached’ bytecode caches
templates_use_cache = BooleanField('templates.use_cache', default=False)

#: Use memcached for bytecode caching
templates_use_memcached_cache = BooleanField('templates.use_memcached_cache', default=False)

#: Use filesystem for bytecode caching
templates_use_filesystem_cache = BooleanField('templates.use_filesystem_cache', default=False)


#TODO: yet a hack untill we have proper information about what an app is

templates_packages_portal = TextField('templates.packages.portal', default=u'inyoka.portal')
templates_packages_news = TextField('templates.packages.news', default=u'inyoka.news')
templates_packages_forum = TextField('templates.packages.forum', default=u'inyoka.forum')
templates_packages_wiki = TextField('templates.packages.wiki', default=u'inyoka.wiki')
templates_packages_paste = TextField('templates.packages.paste', default=u'inyoka.paste')
templates_packages_planet = TextField('templates.packages.planet', default=u'inyoka.planet')

#: Set the caching system.  Choose one of ’null’, ’simple’, ’memcached’ or ’filesystem’.
caching_system = TextField('caching.system', default=u'null')

#: Set the path for the filesystem caches
caching_filesystem_cache_path = TextField('caching.filesystem_cache_path',
                                          default=u'/tmp/_inyoka_cache')

#: Set the timeout for the caching system
caching_timeout = IntegerField('caching.timeout', default=300, min_value=10)

#: Set the memcached servers.  Comma seperated list of memcached servers
caching_memcached_servers = TextField('caching.memcached_servers', default=u'')

#: Set the authsystem to be used.
auth_system = TextField('auth.system', default=u'inyoka.portal.auth.EasyAuth')

# routing specific config values
# values are in the form of `subdomain:/submount`
# if you only apply the submount use `/submount` the `:` will be completed
routing_urls_portal = DottedField('routing.urls.portal', default=u':/')
routing_urls_usercp = DottedField('routing.urls.usercp', default=u':/usercp')
routing_urls_news = DottedField('routing.urls.news', default=u'news:/')
routing_urls_forum = DottedField('routing.urls.forum', default=u'forum:/')
routing_urls_wiki = DottedField('routing.urls.wiki', default=u'wiki:/')
routing_urls_paste = DottedField('routing.urls.paste', default=u'paste:/')
routing_urls_planet = DottedField('routing.urls.planet', default=u'planet:/')
routing_urls_admin = DottedField('routing.urls.admin', default=u'admin:/')
routing_urls_api = DottedField('routing.urls.api', default=u'api:/')
# NEVER CHANGE THAT VALUE!!! TODO: Find a better solution to implement testing
# Url prefixes...
routing_urls_test = DottedField('routing.urls.test', default=u'test:/')
routing_urls_static = DottedField('routing.urls.static', default=u'static:/')
routing_urls_media = DottedField('routing.urls.media', default=u'media:/')


#: Path to the directory that includes static files.  Relative to the inyoka
#: package path.
static_path = TextField('static_path', default=u'static')

#: Path to the directory for shared static files, aka media.  Relative to
#: the inyoka package path.
media_path = TextField('media_path', default=u'media')

#: Name to the wiki index page (the one a user accessing the wiki's ’/’
#: is redirected to)
wiki_index_name = TextField('wiki.index.name', default=u'Main Page')

#: Files with lines greater than this number will not have syntax highlighting.
#: Set zero for no limit.
paste_diffviewer_syntax_highlighting_threshold = IntegerField(
    'paste.diffviewer_syntax_highlighting_threshold', default=0)

# celery broker settings
celery_result_backend = TextField('celery.result_backend', default=u'amqp')
celery_imports = ListField('celery.imports', default=['inyoka.core.tasks'])

# ampq broker settings
broker_host = TextField('broker.host', u'localhost')
broker_port = IntegerField('broker.port', 5672)
broker_user = TextField('broker.user', u'inyoka')
broker_password = TextField('broker.password', u'default')
broker_vhost = TextField('broker.vhost', u'inyoka')
