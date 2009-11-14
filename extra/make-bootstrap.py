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
import os

def after_install(options, home_dir):
    easy_install('Jinja2', home_dir)
    easy_install('Werkzeug==dev', home_dir)
    easy_install('Pygments', home_dir)
    easy_install('SQLAlchemy', home_dir)
    easy_install('sqlalchemy-migrate', home_dir)
    easy_install('simplejson', home_dir)
    easy_install('pytz', home_dir)
    easy_install('nose', home_dir)
    easy_install('Sphinx', home_dir)
    easy_install('html5lib', home_dir)
    easy_install('Babel', home_dir)
    easy_install('coverage', home_dir)
    easy_install('http://dev.pocoo.org/hg/flickzeug-main/archive/tip.tar.gz', home_dir)
    easy_install('http://dev.pocoo.org/hg/bureaucracy-main/archive/tip.tar.gz', home_dir)


def easy_install(package, home_dir, optional_args=None):
    optional_args = optional_args or []
    cmd = [os.path.join(home_dir, 'bin', 'easy_install')]
    cmd.extend(optional_args)
    # update the environment
    cmd.append('-U')
    cmd.append(package)
    call_subprocess(cmd)
"""


def main():
    print virtualenv.create_bootstrap_script(EXTRA_TEXT)


if __name__ == '__main__':
    main()
