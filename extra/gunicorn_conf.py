import logging
import os
import signal
import socket
import sys

#bind = BASE_DOMAIN_NAME
bind = '0.0.0.0:5000'
backlog = 2048

# default workers, special configuration is below
workers = 1

worker_connections = 600
worker_class = 'egg:gunicorn#gevent_pywsgi'
timeout = 30
keepalive = 2
preload = True

debug = False
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
    def monitor():
        modify_times = {}
        while True:
            path = 'gunicorn.trigger'
            try:
                modified = os.stat(path).st_mtime
            except:
                continue
            if path not in modify_times:
                modify_times[path] = modified
                continue
            if modify_times[path] != modified:
                logging.info("%s modified; restarting server", path)
                os.kill(os.getpid(), signal.SIGHUP)
                modify_times = {}
            gevent.sleep(1)

    import gevent
    gevent.spawn(monitor)
