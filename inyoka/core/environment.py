# -*- coding: utf-8 -*-
"""
    inyoka.core.environment
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module can figure how Inyoka is installed and where it has to look
    for shared information.  Currently it knows about two modes: development
    environment and installation on a posix system.  OS X should be special
    cased later and Windows support is missing by now.

    :copyright: (c) 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GPL, see LICENSE for more details.
"""
from os.path import realpath, dirname, join, pardir, isdir


# the path to the contents of the inyoka package
PACKAGE_CONTENTS = realpath(join(dirname(__file__), pardir))

# the path to the folder where the "inyoka" package is stored in.
PACKAGE_LOCATION = realpath(join(PACKAGE_CONTENTS, pardir))

# name of the domain for the builtin translations
LOCALE_DOMAIN = 'messages'

# check development mode first.  If there is a shared folder we must be
# in development mode.
SHARED_DATA = join(PACKAGE_CONTENTS, 'shared')
if isdir(SHARED_DATA):
    MODE = 'development'
    BUILTIN_TEMPLATE_PATH = join(PACKAGE_CONTENTS, 'templates')
    LOCALE_PATH = join(PACKAGE_CONTENTS, 'i18n')

MEDIA_DATA = join(PACKAGE_CONTENTS, 'media')

#TODO: for now we only support a development mode

# get rid of the helpers
del realpath, dirname, join, pardir, isdir
