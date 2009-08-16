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

action_shell = script.make_shell(make_shell)
action_runserver = script.make_runserver(make_app, use_reloader=True)

if __name__ == '__main__':
    script.run()
