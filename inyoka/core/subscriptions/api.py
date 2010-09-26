# -*- coding: utf-8 -*-
"""
    inyoka.core.subscriptions.api
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.resource import IResourceManager
from inyoka.core.subscriptions.models import SubscriptionUnreadObjects, Subscription


class ISubscriptionResourceManager(IResourceManager):
    """Register core models globally."""

    models = (SubscriptionUnreadObjects, Subscription)
