# -*- coding: utf-8 -*-
"""
    inyoka.utils.files
    ~~~~~~~~~~~~~~~~~~

    Various file utils.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from os import listdir
from os.path import join, splitext

def find_unused_filename(folder, filename):
    """
    Find and return an unused file name by appending an id to the file name.

   :param folder: The path to the folder where the file should be placed.
   :param filename: The file's name.
    """
    max_id = 1
    base, ext = splitext(filename)
    # XXX: Escape base
    # XXX: to utils
    r = re.compile('%s(\d+)%s' % (base, ext))
    for f in listdir(folder):
        match = r.match(f)
        if match:
            i = int(match.groups()[0])
            if i > max_id:
                max_id = i
    return '%s%d%s' % (base, max_id + 1, ext)
