# -*- coding: utf-8 -*-
"""
    inyoka.paste.api
    ~~~~~~~~~~~~~~~~

    api description for paste app.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IResource
from inyoka.paste.admin import PasteAdminProvider
from inyoka.paste.services import PasteServices
from inyoka.paste.controllers import PasteController

from inyoka.paste.models import Entry


class PasteResource(IResource):
    models = [Entry]
