# -*- coding: utf-8 -*-
"""
    inyoka.core.api
    ~~~~~~~~~~~~~~~

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
from os.path import join
from inyoka import Interface, deactivated_components
from inyoka.context import ctx
from inyoka.core.resource import IResourceManager
from inyoka.core.config import BooleanConfigField, TextConfigField, \
    IntegerConfigField, DottedConfigField, ListConfigField
from inyoka.core.models import Cache, Confirm, Tag, Storage


#: The default path to media files.
_default_media_data_path = join(os.environ['INYOKA_MODULE'], 'media')


class ICoreResourceManager(IResourceManager):
    """Register core models globally."""

    #: Enable debug mode
    debug = BooleanConfigField('debug', default=False)

    #: Enable testing mode.  Set this to `True` to enable the test mode
    #: of Inyoka.  For example this activates unittest helpers that have
    #: an additional runtime cost which should not be enabled by default.
    #:
    #: This also enables some special logging so that for example our
    #: celery integration does not push forward to celery but executes
    #: tasks directly and adds them to a special container.
    testing = BooleanConfigField('testing', default=False)

    #: The path to the media folder
    media_root = TextConfigField('media_root', default=_default_media_data_path)

    #: The secret key used for hashing the cookies and other
    #: security salting.
    secret_key = TextConfigField('secret_key', default=u'CHANGEME')

    #: Base domain name
    base_domain_name = TextConfigField('base_domain_name', default=u'inyoka.local:5000')

    #: Cookie domain name
    cookie_domain_name = TextConfigField('cookie_domain_name', default=u'.inyoka.local')

    #: Tag uri base, see RFC 4151. May be changed safely. Change this to a real value!
    tag_uri_base = TextConfigField('tag_uri_base', default=u'tag:inyoka.local,1970:inyoka/')

    #: Cookie name
    cookie_name = TextConfigField('cookie_name', default=u'inyoka-session')

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
    permanent_session_lifetime = IntegerConfigField('permanent_session_lifetime', default=30)

    #: Path to the directory that includes static files.  Relative to the inyoka
    #: package path.
    static_path = TextConfigField('static_path', default=u'static')

    #: Exclude inyoka.core.tasks per default to fix the celery loader
    deactivated_components.default.append('inyoka.core.tasks')

    #: register core models
    models = [Cache, Confirm, Tag, Storage]


# Import shortcuts
from inyoka.core.database import db
from inyoka.core.auth.decorators import login_required
from inyoka.core.http import Request, Response, redirect_to, redirect
from inyoka.core.routing import IController, IServiceProvider
from inyoka.core.routing import view, service, Rule, href
from inyoka.core.templating import templated, render_template
from inyoka.core.middlewares import IMiddleware
from inyoka.core.cache import cache
from inyoka.core.serializer import SerializableObject
from inyoka.utils.logger import logger
from inyoka.i18n import _, gettext, ngettext, lazy_gettext, lazy_ngettext
from inyoka.core import exceptions as exc
