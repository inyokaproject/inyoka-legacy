# -*- coding: utf-8 -*-
"""
    inyoka.event.api
    ~~~~~~~~~~~~~~~~

    api description for event app.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IResourceManager
from inyoka.event.models import Event, event_tag


class EventResourceManager(IResourceManager):
    models = [Event, event_tag]
