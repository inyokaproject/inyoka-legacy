# -*- coding: utf-8 -*-
"""
    inyoka.utils
    ~~~~~~~~~~~~

    Various utilities.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import escape as wzescape


def patch_wrapper(decorator, base):
    decorator.__name__ = base.__name__
    decorator.__module__ = base.__module__
    decorator.__doc__ = base.__doc__
    decorator.__dict__ = base.__dict__
    return decorator

def escape(s, quote=True):
    """Like `werkzeug.escape`, but with `quote` set to True per default."""
    return wzescape(s, quote)
