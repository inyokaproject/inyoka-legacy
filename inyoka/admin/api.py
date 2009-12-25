# -*- coding: utf-8 -*-
"""
    inyoka.admin.api
    ~~~~~~~~~~~~~~~~

    API module for the Inyoka admin center.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import Interface


class IAdminProvider(Interface):

    #: The internal id for the admin interface
    name = None

    #: The public display name.  Please use the i18n interface!
    title = None

    #: The public url map
    url_map = None
