# -*- coding: utf-8 -*-
"""
    inyoka.core.api
    ~~~~~~~~~~~~~~~

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
#TODO: Sort everything here a bit and define the API properly.
#      Maybe this module should not do anything more than all other
#      apps `api` modules but define the interfaces and the resource-components
#      and should not import other core packages.
#      This way we don't get cluttered

# Imports for easy API access and our import system
from inyoka import Interface
from inyoka.context import ctx
from inyoka.core.resource import IResourceManager


from inyoka.core.models import Cache, Confirm, Tag, Storage

import os
from os.path import join
from inyoka.core.config import BooleanConfigField, TextConfigField, \
    IntegerConfigField, DottedConfigField, ListConfigField


_default_media_data_path = join(os.environ['INYOKA_MODULE'], 'media')


class ICoreResourceManager(IResourceManager):
    """Register core models globally."""

    #: Enable debug mode
    debug = BooleanConfigField('debug', default=False)

    #: The path to the media folder
    media_root = TextConfigField('media_root', default=_default_media_data_path)

    #: The secret key used for hashing the cookies and other
    #: security salting.
    secret_key = TextConfigField('secret_key', default=u'CHANGEME')

    #: Base domain name
    base_domain_name = TextConfigField('base_domain_name', default=u'inyoka.local:5000')

    #: Cookie domain name
    cookie_domain_name = TextConfigField('cookie_domain_name', default=u'.inyoka.local')

    #: Cookie name
    cookie_name = TextConfigField('cookie_name', default=u'inyoka-session')

    #: The current language locale
    language = TextConfigField('language', default=u'en')

    #: The default timezone for all users
    default_timezone = TextConfigField('default_timezone', default=u'Europe/Berlin')

    #: The name of the anonymous user
    anonymous_name = TextConfigField('anonymous_name', default=u'anonymous')

    #: Enable or disable CSRF Protection
    enable_csrf_checks = BooleanConfigField('enable_csrf_checks', default=True)

    #: The website title to show in various places
    website_title = TextConfigField('website_title', default=u'Inyoka Portal')

    #: The mail address used for sending mails
    mail_address = TextConfigField('mail_address', default=u'system@inyoka.local')

    #: The duration a permanent session is valid.  Defined in days, defaults to 30
    permanent_session_lifetime = IntegerConfigField('permanent_session_life', default=30)

    #: Path to the directory that includes static files.  Relative to the inyoka
    #: package path.
    static_path = TextConfigField('static_path', default=u'static')

    #: Path to the directory for shared static files, aka media.  Relative to
    #: the inyoka package path.
    media_path = TextConfigField('media_path', default=u'media')

    models = [Cache, Confirm, Tag, Storage]



from inyoka.core.database import db
from inyoka.core.auth import login_required
from inyoka.core.http import Request, Response, redirect_to, redirect, get_bound_request
from inyoka.core.routing import IController, IServiceProvider
from inyoka.core.routing import view, service, Rule, href
from inyoka.core.templating import templated, render_template
from inyoka.core.middlewares import IMiddleware
from inyoka.core.cache import cache
from inyoka.core.serializer import SerializableObject
from inyoka.utils.logger import logger
from inyoka.i18n import _, gettext, ngettext, lazy_gettext, lazy_ngettext
from inyoka.core import exceptions as exc
