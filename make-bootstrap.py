#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Inyoka Bootstrap Creation Script
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Creates a bootstrap script for inyoka.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

import virtualenv

EXTRA_TEXT = """
import tempfile, shutil, os

def after_install(options, home_dir):
    easy_install('Jinja2', home_dir)
    easy_install('Werkzeug', home_dir)
    easy_install('Pygments', home_dir)
    easy_install('SQLAlchemy==0.5.5', home_dir)
    easy_install('sqlalchemy-migrate', home_dir)
    easy_install('simplejson', home_dir)
    easy_install('pytz', home_dir)
    easy_install('html5lib', home_dir)
    easy_install('Babel', home_dir)
"""

def main():
    print virtualenv.create_bootstrap_script(EXTRA_TEXT)

if __name__ == '__main__':
    main()
