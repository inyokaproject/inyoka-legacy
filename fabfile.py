# -*- coding: utf-8 -*-
"""
    Fabfile for Inyoka
    ~~~~~~~~~~~~~~~~~~

    This script is used by fabric for easy deployment.

    :copyright: Copyright 2009 by the Inyoka Team.
    :license: GNU GPL.
"""

import tempfile

set(
    fab_user = 'ubuntu_de',
    inyoka_repo = 'http://hg.ubuntu-eu.org/ubuntu-de-inyoka/',
)

    config.fab_user = 'ubuntu_de'
    config.inyoka_repo = 'http://hg.ubuntu-eu.org/ubuntu-de-inyoka/'
    config.target_dir = '~/virtualenv'


def test():
    config.fab_hosts = ['127.0.0.1']

def staging():
    config.fab_hosts = ['staging.ubuntuusers.de']

def production():
    config.fab_hosts = ['dongo.ubuntu-eu.org', 'unkul.ubuntu-eu.org']

def bootstrap():
    """Create a virtual environment.  Call this once on every new server."""
    let(
        fab_hosts = [x.strip() for x in raw_input('Servers: ').split(',')],
        python_interpreter = raw_input('Python-executable (default: python2.5): ').strip() or 'python2.5',
        target_dir = raw_input('Location (default: ~/virtualenv): ').strip().rstrip('/') or '~/virtualenv',
    )
    bootstrap = tempfile.mktemp(".py", "fabric_")
    run('mkdir $(target_dir)')
    run('hg clone $(inyoka_repo) $(target_dir)/inyoka')
    local("$(python_interpreter) make-bootstrap.py > '%s'" % bootstrap)
    put(bootstrap, 'bootstrap.py')
    run('unlet PYTHONPATH; $(python_interpreter) bootstrap.py --no-site-packages $(target_dir)')
    run("ln -s $(target_dir)/inyoka/inyoka $(target_dir)/lib/python`$(python_interpreter) -V 2>&1|grep -o '[0-9].[0-9]'`/site-packages")

def deploy():
    """Update Inyoka and touch the wsgi file"""
    require('fab_hosts', provided_by = [test, staging, production])
    run('cd $(target_dir)/inyoka; hg pull -u')
