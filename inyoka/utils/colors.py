#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.utils.colors
    ~~~~~~~~~~~~~~~~~~~

    Add Support for colorized Command Line Output

    This script is based on the pocoo ones (www.pocoo.org)
    witch was taken from Gentoo.

    You can use a color in the following format::

        bold('This Text is Bold-Formatted')

    Please note, that Windows doesn't support this colors.
    So if you work at Windows use the `nocolor` function, to disable
    the command line colors.

    :copyright: 1998-2004 by the Gentoo Foundation.
    :copyright: 2006-2007 by Georg Brandl and Christopher Grebs
    :license: GNU GPL, see LICENSE for more details.
"""

esc_seq = '\x1b['

codes = {}
codes['reset'] = esc_seq + '39;49;00m'

codes['bold'] = esc_seq + '01m'
codes['underline'] = esc_seq + '04m'

ansi_color_codes = []
for x in xrange(30, 38):
    ansi_color_codes.append('%im' % x)
    ansi_color_codes.append('%i;01m' % x)


rgb_ansi_colors = [
    '0x000000', '0x555555', '0xAA0000', '0xFF5555',
    '0x00AA00', '0x55FF55', '0xAA5500', '0xFFFF55',
    '0x0000AA', '0x5555FF', '0xAA00AA', '0xFF55FF',
    '0x00AAAA', '0x55FFFF', '0xAAAAAA', '0xFFFFFF'
]

for x in xrange(len(rgb_ansi_colors)):
    codes[rgb_ansi_colors[x]] = esc_seq + ansi_color_codes[x]

del x

codes["black"]     = codes["0x000000"]
codes["darkgray"]  = codes["0x555555"]

codes["red"]       = codes["0xFF5555"]
codes["darkred"]   = codes["0xAA0000"]

codes["green"]     = codes["0x55FF55"]
codes["darkgreen"] = codes["0x00AA00"]

codes["yellow"]    = codes["0xFFFF55"]
codes["brown"]     = codes["0xAA5500"]

codes["blue"]      = codes["0x5555FF"]
codes["darkblue"]  = codes["0x0000AA"]

codes["fuchsia"]   = codes["0xFF55FF"]
codes["purple"]    = codes["0xAA00AA"]

codes["teal"]      = codes["0x00AAAA"]
codes["turquoise"] = codes["0x55FFFF"]

codes["white"]     = codes["0xFFFFFF"]
codes["lightgray"] = codes["0xAAAAAA"]

codes["darkteal"]   = codes["turquoise"]
codes["darkyellow"] = codes["brown"]
codes["fuscia"]     = codes["fuchsia"]
codes["white"]      = codes["bold"]

def nocolor():
    """turn off colorization
    """
    for code in codes:
        codes[code] = ""

def reset_color():
    """
    >>> reset_color()
    '\\x1b[39;49;00m'
    """
    return codes["reset"]

def colorize(color_key, text):
    """
    >>> colorize("fuscia", "test")
    '\\x1b[35;01mtest\\x1b[39;49;00m'
    """
    return codes[color_key] + text + codes["reset"]

functions_colors = [
    "bold", "white", "teal", "turquoise", "darkteal",
    "fuscia", "fuchsia", "purple", "blue", "darkblue",
    "green", "darkgreen", "yellow", "brown",
    "darkyellow", "red", "darkred", "underline"
]

def create_color_func(color_key):
    """
    Return a function that formats its argument in the given color.

    >>> create_color_func("fuscia")("test")
    '\\x1b[35;01mtest\\x1b[39;49;00m'
    """
    def derived_func(text):
        return colorize(color_key, text)
    return derived_func

ns = locals()
for c in functions_colors:
    ns[c] = create_color_func(c)

del c, ns
