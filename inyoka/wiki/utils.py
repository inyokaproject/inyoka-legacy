# -*- coding: utf-8 -*-
"""
    inyoka.wiki.utils
    ~~~~~~~~~~~~~~~~~

    Utilities for the wiki.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

def urlify_page_name(name):
    return name.replace(' ', '_')

def deurlify_page_name(name):
    return name.replace('_', ' ')
