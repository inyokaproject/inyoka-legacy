# -*- coding: utf-8 -*-
"""
    inyoka.utils
    ~~~~~~~~~~~~

    Various utilities.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import import_string as wimport_string


def import_string(import_name, silent=False):
    """A customized version of import_string that converts
    `import_name` to an ascii string because there are some crazy
    bugs with __import__ working with unicode strings.
    """
    if isinstance(import_name, unicode):
        import_name = import_name.encode('ascii')
    return wimport_string(import_name, silent)
