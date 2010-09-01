# -*- coding: utf-8 -*-
"""
    inyoka.paste.utils
    ~~~~~~~~~~~~~~~~~~

    Various utilities for our pastebin.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import difflib
from markupsafe import Markup
from inyoka.core.api import ctx
from inyoka.utils.highlight import highlight_text


def generate_highlighted_udiff(old, new, old_title='', new_title='',
                   context_lines=4, old_lang=None, new_lang=None):
    """
    Generate an udiff out of two texts.  If titles are given they will be
    used on the diff.  `context_lines` defaults to 5 and represents the
    number of lines used in an udiff around a changed line.

    This is a special version that enables syntax highlighting between pastes.
    """
    threshold = ctx.cfg['paste.diffviewer_syntax_highlighting_threshold']
    old_lines = len(old.splitlines())
    new_lines = len(new.splitlines())

    # highlight if the threshold allows it.
    if not (threshold and (old_lines > threshold or new_lines > threshold)):
        old = highlight_text(old, old_lang, inline=True)
        new = highlight_text(new, new_lang, inline=True)

    return Markup(u'\n'.join(difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        fromfile=old_title,
        tofile=new_title,
        lineterm='',
        n=context_lines
    )))
