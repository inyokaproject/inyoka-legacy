#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Inyoka Management Script
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Starts server and debugger.  This script may never globally import stuff
    from inyoka as the migrations have to load the SQLAlchemy database layout
    without invoking the autoloading mechanism of the tables.  Otherwise it
    will be impossible to use them.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sys
from werkzeug import script
from werkzeug.debug import DebuggedApplication
from werkzeug.contrib import profiler


def make_app():
    import inyoka.utils.http
    from inyoka.conf import settings
    from inyoka.application import application, StaticDomainHandler
    app = application
    app = StaticDomainHandler(app)
    if settings.DEBUG:
        app = DebuggedApplication(app, evalex=settings.ENABLE_DEBUGGER)
    return app


action_shell = script.make_shell(lambda: {})
action_profiled = profiler.make_action(make_app, '', 8080)


def action_repoze_profiled(discard_first_request=True, flush=True):
    from repoze.profile.profiler import AccumulatingProfileMiddleware
    from werkzeug import run_simple
    from inyoka.conf import settings
    app = AccumulatingProfileMiddleware(
        make_app(),
        log_filename='./repoze_profile.log',
        cachegrind_filename='./cachegrind.out',
        discard_first_request=discard_first_request,
        flush_at_shutdown=flush,
        path = '/__profile__')
    run_simple(settings.DEVSERVER_HOST, settings.DEVSERVER_PORT, app, True,
               False, False, False, 1)


def action_runserver():
    from inyoka.conf import settings
    return script.make_runserver(make_app, settings.DEVSERVER_HOST,
                                 settings.DEVSERVER_PORT,
                                 use_reloader=True)
action_runserver = action_runserver()


def action_create_superuser(username='', email='', password=''):
    """
    Create a user with all privileges.  If you don't provide an argument
    the script will prompt you for it.
    """
    from getpass import getpass
    while not username:
        username = raw_input('username: ')
    while not email:
        email = raw_input('email: ')
    if not password:
        while not password:
            password = getpass('password: ')
            if password:
                if password == getpass('repeat: '):
                    break
                password = ''
    from inyoka.portal.user import User, PERMISSION_NAMES
    from inyoka.forum.models import Forum, Privilege
    from inyoka.forum.acl import PRIVILEGES_DETAILS, join_flags
    from inyoka.utils.database import db
    user = User.query.register_user(username, email, password, False)
    permissions = 0
    for perm in PERMISSION_NAMES.keys():
        permissions |= perm
    user._permissions = permissions
    db.session.commit()
    bits = dict(PRIVILEGES_DETAILS).keys()
    bits = join_flags(*bits)
    for forum in Forum.query.all():
        privilege = Privilege(
            user=user,
            forum=forum,
            positive=bits
        )
    db.session.commit()
    print 'created superuser'


def action_runcp(hostname='0.0.0.0', port=8080):
    """Run the application in CherryPy."""
    from cherrypy.wsgiserver import CherryPyWSGIServer
    server = CherryPyWSGIServer((hostname, port), make_app())
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


def action_dbshell():
    import sys
    from subprocess import Popen
    from sqlalchemy.engine.url import make_url
    from inyoka.conf import settings
    url = make_url(settings.DATABASE_URI)

    #TODO: add more drivers here and use special database options
    cmd = []
    if url.drivername == 'mysql':
        cmd.extend(('mysql', url.database))
        if url.username:
            cmd.extend(('-u', url.username))
        if url.password:
            cmd.extend((('-p%s' % url.password),))
        if url.host:
            cmd.extend(('-h', url.host))
        if url.port:
            cmd.extend(('-P', url.port))
    elif url.drivername == 'sqlite':
        cmd.extend(('sqlite3', url.database))

    p = Popen(cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
    return p.wait()


if __name__ == '__main__':
    script.run()
