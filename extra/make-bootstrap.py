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
# virtualenv is stored wrong in debian squeeze
try:
    from virtualenv import create_bootstrap_script
except ImportError:
    from virtualenv.virtualenv import create_bootstrap_script


EXTRA_TEXT = """
import os
import tempfile, shutil
from os import path

pil_version = '1.1.7'
cldr_version = '1.7.2'


def install_requirements(home_dir, requirements):
    if not requirements:
        return
    home_dir = os.path.abspath(home_dir)
    cmd = [os.path.join(home_dir, 'bin', 'pip')]
    cmd.extend(['install', '-r', os.path.join(home_dir, requirements)])
    call_subprocess(cmd)


def pil_install(home_dir):
    folder = tempfile.mkdtemp(prefix='virtualenv')

    call_subprocess(FETCH_CMD + ['http://effbot.org/downloads/Imaging-%s.tar.gz' % pil_version], cwd=folder)
    call_subprocess(['tar', '-xzf', 'Imaging-%s.tar.gz' % pil_version], cwd=folder)

    img_folder = path.join(folder, 'Imaging-%s' % pil_version)

    f1 = path.join(img_folder, 'setup_new.py')
    f2 = path.join(img_folder, 'setup.py')

    file(f1, 'w').write(file(f2).read().replace('import _tkinter', 'raise ImportError()'))

    cmd = [path.join(home_dir, 'bin', 'python')]
    cmd.extend([path.join(os.getcwd(), f1), 'install'])
    call_subprocess(cmd)

    shutil.rmtree(folder)


def babel_svn_repo_install(home_dir):
    folder = tempfile.mkdtemp(prefix='virtualenv')
    pypath = path.join(home_dir, 'bin', 'python')

    # checkout cldr
    call_subprocess(FETCH_CMD + ['http://unicode.org/Public/cldr/%s/core.zip' % cldr_version], cwd=folder)
    call_subprocess(['unzip', '-d', 'cldr', 'core.zip'], cwd=folder)
    cldr_folder = path.join(folder, 'cldr', 'common')

    # checkout babel and import/compile respective cldr
    call_subprocess(['svn', 'co', 'http://svn.edgewall.org/repos/babel/trunk/', 'babel'], cwd=folder)
    babel_folder = path.join(folder, 'babel')
    cmd = [pypath]
    cmd.extend([path.join(os.getcwd(), babel_folder, 'scripts/import_cldr.py'),
                cldr_folder])
    call_subprocess(cmd)

    cmd = [path.abspath(path.join(home_dir, 'bin', 'python'))]
    cmd.extend([path.join(os.getcwd(), path.join(babel_folder, 'setup.py')), 'install'])
    call_subprocess(cmd, cwd=babel_folder)
    shutil.rmtree(folder)


def after_install(options, home_dir):
    global FETCH_CMD
    try:
        call_subprocess(['which', 'wget'], show_stdout=False)
        FETCH_CMD = ['wget']
    except OSError:
        # wget does not exist, try curl instead
        try:
            call_subprocess(['which', 'curl'], show_stdout=False)
            FETCH_CMD = ['curl', '-L', '-O']
        except OSError:
            import sys
            sys.stderr.write('\\nERROR: need either wget or curl\\n')
            sys.exit(1)

    easy_install('setuptools', home_dir)
    babel_svn_repo_install(home_dir)
    install_requirements(home_dir, options.requirements)
    pil_install(home_dir)


def easy_install(package, home_dir, optional_args=None):
    optional_args = optional_args or []
    cmd = [path.join(home_dir, 'bin', 'easy_install')]
    cmd.extend(optional_args)
    # update the environment
    cmd.append('-U')
    cmd.append('-O2')
    cmd.append(package)
    call_subprocess(cmd)


def extend_parser(parser):
    parser.add_option('-r', '--requirements', dest='requirements',
                      default='',
                      help='Path to a requirements file usable with pip')

"""


cmdlineparser = OptionParser()
cmdlineparser.add_option('-p', '--python', dest='python',
                         default='',
                         help='python version to use (like 2.5)')


if __name__ == '__main__':
    (options, args) = cmdlineparser.parse_args()
    print create_bootstrap_script(EXTRA_TEXT, python_version=options.python)
