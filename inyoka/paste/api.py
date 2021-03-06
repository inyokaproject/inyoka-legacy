# -*- coding: utf-8 -*-
"""
    inyoka.paste.api
    ~~~~~~~~~~~~~~~~

    api description for paste app.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import IResourceManager
from inyoka.core.config import IntegerConfigField
from inyoka.paste.models import PasteEntry


class PasteResourceManager(IResourceManager):

    #: Files with lines greater than this number will not have syntax highlighting.
    #: Set zero for no limit.
    paste_diffviewer_syntax_highlighting_threshold = IntegerConfigField(
        'paste.diffviewer_syntax_highlighting_threshold', default=0)

    models = [PasteEntry]
