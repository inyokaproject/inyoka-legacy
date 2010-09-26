#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Inyoka Bootstrap Creation Script
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Creates a bootstrap script for inyoka.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

from optparse import OptionParser
from os.path import isdir
# virtualenv is stored wrong in debian squeeze
try:
    from virtualenv import create_bootstrap_script
except ImportError:
    from virtualenv.virtualenv import create_bootstrap_script

extratext = file('extra/bootstrap-extra.py','r')
EXTRA_TEXT = extratext.read()
extratext.close()

if __name__ == '__main__':
    print create_bootstrap_script(EXTRA_TEXT)
