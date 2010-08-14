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
from inyoka.core.database import db
from inyoka.core.auth import login_required
from inyoka.core.http import Request, Response, redirect_to, redirect, get_bound_request
from inyoka.core.routing import IController, IServiceProvider
from inyoka.core.routing import view, service, Rule, href
from inyoka.core.templating import templated, render_template
from inyoka.core.middlewares import IMiddleware
from inyoka.core.exceptions import *
from inyoka.core.cache import cache
from inyoka.core.serializer import SerializableObject
from inyoka.utils.logger import logger
from inyoka.i18n import *



from inyoka.core.cache import Cache
from inyoka.core.models import Confirm, Tag
from inyoka.core.subscriptions.models import SubscriptionUnreadObjects, \
    Subscription
from inyoka.core.storage import Storage
from inyoka.core.auth.models import User, UserProfile, Group, group_group, \
    user_group

class ICoreResourceManager(IResourceManager):
    """Register core models globally."""
    models = [
        # core utility models
        Storage, Confirm, Tag, Cache,
        # subscription models
        SubscriptionUnreadObjects, Subscription,
        # auth models
        User, UserProfile, Group, group_group, user_group,
    ]
