#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Inyoka Management Script
    ~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import script

def make_app():
    from inyoka.application import application
    return application

def make_shell():
    application = make_app()
    return locals()

def action_dbshell():
    import sys
    from subprocess import Popen
    from sqlalchemy.engine.url import make_url
    from inyoka.core.config import config
    url = make_url(config['database_uri'])

    #TODO: add more drivers here and use special database options
    cmd = []
    if url.drivername == 'mysql':
        cmd.extend(('mysql', url.database))
        if url.username:
            cmd.extend(('-u', url.username))
        if url.password:
            cmd.append('-p%s' % url.password)
        if url.host:
            cmd.extend(('-h', url.host))
        if url.port:
            cmd.extend(('-P', url.port))
    elif url.drivername == 'sqlite':
        cmd.extend(('sqlite3', url.database))

    p = Popen(cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
    return p.wait()

action_shell = script.make_shell(make_shell, 'Interactive Inyoka Shell')
action_runserver = script.make_runserver(make_app, use_reloader=True)

if __name__ == '__main__':
    script.run()
