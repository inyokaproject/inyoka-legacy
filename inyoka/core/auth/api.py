# -*- coding: utf-8 -*-
"""
    inyoka.core.auth.api
    ~~~~~~~~~~~~~~~~~~~~

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.resource import IResourceManager
from inyoka.core.config import TextConfigField
from inyoka.core.auth.models import User, UserProfile, Group, group_group, \
    user_group


class IAuthResourceManager(IResourceManager):
    """Register core models globally."""

    #: The name of the anonymous user
    anonymous_name = TextConfigField('anonymous_name', default=u'anonymous')

    #: Set the authsystem to be used.
    auth_system = TextConfigField('auth.system', default=u'inyoka.portal.auth.EasyAuth')

    models = [User, UserProfile, Group, group_group, user_group]
