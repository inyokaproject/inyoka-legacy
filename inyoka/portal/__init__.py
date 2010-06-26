# -*- coding: utf-8 -*-
"""
    inyoka.portal
    ~~~~~~~~~~~~~

    The portal component is providing user centric stuff like profiles and
    messaging.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.portal.auth import EasyAuth, HttpBasicAuth
from inyoka.portal.admin import PortalAdminController
from inyoka.portal.models import BasicProfile
from inyoka.portal.controllers import PortalController, CalendarController
