# -*- coding: utf-8 -*-
"""
    inyoka.forum
    ~~~~~~~~~~~~

    Our bulletin board implementation.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.forum.admin import ForumAdminProvider
from inyoka.forum.models import ForumSchemaController, QuestionsContentProvider
from inyoka.forum.controllers import ForumController
