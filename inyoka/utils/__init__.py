# -*- coding: utf-8 -*-
"""
    inyoka.utils
    ~~~~~~~~~~~~

    Various utilities.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sys
from math import sqrt
from werkzeug import import_string


def flatten_iterator(iter):
    """Flatten an iterator to one without any sub-elements"""
    for item in iter:
        if hasattr(item, '__iter__'):
            for sub in flatten_iterator(item):
                yield sub
        else:
            yield item


# Algorithm taken from code.reddit.com by CondeNet, Inc.
def confidence(ups, downs):
    """Confidence sort, see
    http://www.evanmiller.org/how-not-to-sort-by-average-rating.html
    """
    n = float(ups + downs)
    if n == 0:
        return 0
    z = 1.0 #1.0 = 85%, 1.6 = 95%
    phat = float(ups) / n
    return sqrt(phat+z*z/(2*n)-z*((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n)


def safe_import_string(module_name):
    """Import a module safely by rollback after a failed import."""
    already_imported = sys.modules.copy()
    try:
        return import_string(module_name, silent=False)
    except:
        for modname in sys.modules.copy():
            if not modname in already_imported:
                del sys.modules[modname]
        raise
