# -*- coding: utf-8 -*-
"""
    Inyoka Bootstrap Creation Script
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Creates a bootstrap script for inyoka.

    :copyright: Copyright 2008 by Florian Apolloner.
    :license: GNU GPL.
"""

import virtualenv

EXTRA_TEXT = """
import tempfile, shutil, os

xapian_version = '1.0.14'
pil_version = '1.1.6'

def easy_install(package, home_dir, optional_args=None):
    optional_args = optional_args or []
    cmd = [os.path.join(home_dir, 'bin', 'easy_install')]
    cmd.extend(optional_args)
    # update the environment
    cmd.append('-U')
    cmd.append(package)
    call_subprocess(cmd)

def xapian_install(home_dir):
    folder = tempfile.mkdtemp(prefix='virtualenv')
    prefix=os.path.join(home_dir, 'lib')

    call_subprocess(['wget', 'http://oligarchy.co.uk/xapian/%s/xapian-core-%s.tar.gz' %
                    (xapian_version, xapian_version)], cwd=folder)
    call_subprocess(['tar', '-xzf', 'xapian-core-%s.tar.gz' % xapian_version], cwd=folder)
    call_subprocess(['wget', 'http://oligarchy.co.uk/xapian/%s/xapian-bindings-%s.tar.gz' %
                    (xapian_version, xapian_version)], cwd=folder)
    call_subprocess(['tar', '-xzf', 'xapian-bindings-%s.tar.gz' % xapian_version], cwd=folder)

    core_folder = os.path.join(folder, 'xapian-core-' + xapian_version)
    call_subprocess(['./configure', '--prefix', prefix], cwd=core_folder)
    call_subprocess(['make'], cwd=core_folder)
    call_subprocess(['make', 'install'], cwd=core_folder)

    binding_folder = os.path.join(folder, 'xapian-bindings-' + xapian_version)
    call_subprocess(['./configure', '--with-python', '--prefix', prefix], extra_env={
        'PYTHON':           os.path.join(home_dir, 'bin', 'python'),
        'XAPIAN_CONFIG':    os.path.join(folder, 'xapian-core-' +
                                         xapian_version, 'xapian-config')
    }, cwd=binding_folder)
    call_subprocess(['make'], cwd=binding_folder)
    call_subprocess(['make', 'install'], cwd=binding_folder)

    shutil.rmtree(folder)

def pil_install(home_dir):
    folder = tempfile.mkdtemp(prefix='virtualenv')

    call_subprocess(['wget', 'http://effbot.org/downloads/Imaging-%s.tar.gz' % pil_version], cwd=folder)
    call_subprocess(['tar', '-xzf', 'Imaging-%s.tar.gz' % pil_version], cwd=folder)

    img_folder = os.path.join(folder, 'Imaging-%s' % pil_version)

    f1 = os.path.join(img_folder, 'setup_new.py')
    f2 = os.path.join(img_folder, 'setup.py')

    file(f1, 'w').write(file(f2).read().replace('import _tkinter', 'raise ImportError()'))

    cmd = [os.path.join(home_dir, 'bin', 'python')]
    cmd.extend([os.path.join(os.getcwd(), f1), 'install'])
    call_subprocess(cmd)

    shutil.rmtree(folder)

def after_install(options, home_dir):
    print 'On errors execute the following commands on the machine first:'
    print '  apt-get install libmemcache-dev libxapian-dev python-dev'
    print '  apt-get build-dep python-mysqldb python-imaging'
    print
    easy_install('Jinja2', home_dir)
    easy_install('Werkzeug', home_dir)
    easy_install('Pygments', home_dir)
    easy_install('SQLAlchemy==0.5.5', home_dir)
    easy_install('sqlalchemy-migrate', home_dir)
    easy_install('simplejson', home_dir)
    easy_install('pytz', home_dir)
    easy_install('html5lib', home_dir)
    easy_install('dnspython', home_dir)
    easy_install('wsgiref', home_dir)
    easy_install('MySQL-python', home_dir)
    easy_install('http://feedparser.googlecode.com/files/feedparser-4.1.zip', home_dir)
    easy_install('python-memcached', home_dir)
    easy_install('cssutils', home_dir)
    easy_install('coverage', home_dir)
    easy_install('http://bitbucket.org/jek/translitcodec/get/tip.zip', home_dir)
    easy_install('Babel', home_dir)
    xapian_install(os.path.abspath(home_dir))
    pil_install(os.path.abspath(home_dir))
"""

def main():
    print virtualenv.create_bootstrap_script(EXTRA_TEXT)

if __name__ == '__main__':
    main()
