import logging
import os
import signal
import socket
import sys
import commands
import thread
import time
import inyoka
from itertools import chain
from werkzeug.serving import reloader_loop
from gunicorn.sock import create_socket


#bind = BASE_DOMAIN_NAME
bind = '0.0.0.0:5000'
backlog = 2048

# default workers, special configuration is below
workers = 1

worker_connections = 600
#worker_class = 'egg:gunicorn#gevent_pywsgi'
worker_class = 'egg:gunicorn#sync'
timeout = 30
keepalive = 2
preload = True

debug = True
spew = False

daemon = False
pidfile = '/tmp/gunicorn_inyoka.pid'
umask = 0
user = None
group = None
tmp_upload_dir = None

#
# Logging
#
# logfile - The path to a log file to write to.
#
# A path string. "-" means log to stdout.
#
# loglevel - The granularity of log output
#
# A string of "debug", "info", "warning", "error", "critical"
#

logfile = '/var/log/www/gunicorn_de/error.log'
logfile = '-'
loglevel = 'debug'

proc_name = 'inyoka'


def after_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)" % worker.pid)

def before_fork(server, worker):
    pass

def before_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    extra_files = []

    def monitor():
        def iter_module_files():
            for module in sys.modules.values():
                filename = getattr(module, '__file__', None)
                if filename:
                    old = None
                    while not os.path.isfile(filename):
                        old = filename
                        filename = os.path.dirname(filename)
                        if filename == old:
                            break
                    else:
                        if filename[-4:] in ('.pyc', '.pyo'):
                            filename = filename[:-1]
                        yield filename

        mtimes = {}
        while True:
            for filename in chain(iter_module_files(), extra_files or ()):
                try:
                    mtime = os.stat(filename).st_mtime
                except OSError:
                    continue

                old_time = mtimes.get(filename)
                if old_time is None:
                    mtimes[filename] = mtime
                    continue
                elif mtime > old_time:
                    server.log.info(' * Detected change in %r, reloading' % filename)
                    for (pid, worker) in list(server.WORKERS.items()):
                        server.kill_worker(pid, signal.SIGQUIT)
                    mtimes = {}
            time.sleep(1)

    thread.start_new_thread(monitor, ())
