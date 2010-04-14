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
from virtualenv import create_bootstrap_script

EXTRA_TEXT = """
import os
import tempfile, shutil

pil_version = '1.1.7'


def pil_install(home_dir):
    folder = tempfile.mkdtemp(prefix='virtualenv')

    call_subprocess(['wget', 'http://effbot.org/downloads/Imaging-%s.tar.gz' % pil_version], cwd=folder)
    call_subprocess(['tar', '-xzf', 'Imaging-%s.tar.gz' % pil_version], cwd=folder)

    img_folder = os.path.join(folder, 'Imaging-%s' % pil_version)

    f1 = os.path.join(img_folder, 'setup_new.py')
    f2 = os.path.join(img_folder, 'setup.py')

    file(f1, 'w').write(file(f2).read().replace('import _tkinter', 'raise ImportError()'))

    cmd = ['CFLAGS="-fPIC -DPIC" ', os.path.join(home_dir, 'bin', 'python')]
    cmd.extend([os.path.join(os.getcwd(), f1), 'install'])
    call_subprocess(cmd)

    shutil.rmtree(folder)


def after_install(options, home_dir):
    easy_install('setuptools', home_dir)
    easy_install('Jinja2', home_dir)
    easy_install('Werkzeug', home_dir)
    easy_install('Pygments', home_dir)
    easy_install('simplejson', home_dir)
    easy_install('pytz', home_dir)
    easy_install('nose', home_dir)
    easy_install('Sphinx', home_dir)
    easy_install('html5lib', home_dir)
    easy_install('Babel', home_dir)
    easy_install('coverage', home_dir)
    easy_install('minimock', home_dir)
    easy_install('Fabric', home_dir)
    easy_install('http://hg.sqlalchemy.org/sqlalchemy/archive/tip.tar.gz', home_dir)
    easy_install('http://dev.pocoo.org/hg/flickzeug-main/archive/tip.tar.gz', home_dir)
    easy_install('http://dev.pocoo.org/hg/bureaucracy-main/archive/tip.tar.gz', home_dir)
    easy_install('lxml', home_dir)
    pil_install(home_dir)


def easy_install(package, home_dir, optional_args=None):
    optional_args = optional_args or []
    cmd = [os.path.join(home_dir, 'bin', 'easy_install')]
    cmd.extend(optional_args)
    # update the environment
    cmd.append('-U')
    cmd.append(package)
    call_subprocess(cmd)
"""


cmdlineparser = OptionParser()
cmdlineparser.add_option('-p', '--python', dest='python',
                         default='',
                         help='python version to use (like 2.5)')


if __name__ == '__main__':
    (options, args) = cmdlineparser.parse_args()
    print create_bootstrap_script(EXTRA_TEXT,python_version=options.python)
