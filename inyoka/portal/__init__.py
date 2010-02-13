# -*- coding: utf-8 -*-
"""
    inyoka.portal
    ~~~~~~~~~~~~~

    The portal component is providing user centric stuff like profiles and
    messaging.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka import Interface
from inyoka.core import auth
from inyoka.core.context import ctx
from inyoka.core.database import IModelPropertyProvider

class IUserProfileExtender(IModelPropertyProvider, Interface):
    model = auth.User

    @classmethod
    def get_profile_names(cls, only_editable=False):
        fields = []
        for imp in ctx.get_implementations(cls):
            fields += imp.properties.keys()
        return fields
