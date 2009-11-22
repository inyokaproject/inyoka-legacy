# -*- coding: utf-8 -*-
"""
    inyoka.utils
    ~~~~~~~~~~~~

    Various utilities.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import escape as wzescape


def escape(s, quote=True):
    """Like `werkzeug.escape`, but with `quote` set to True per default."""
    return wzescape(s, quote)
