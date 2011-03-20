============
Installation
============

.. todo:

   This documentation is a bit distribution dependent, try to abstract it.

Dependencies and Virtual Environment
====================================

To get Inyoka work properly we need those dependencies (with headers):
 * Python (at least 2.6)
 * python-setuptools
 * mercurial
 * subversion
 * fabric
 * unzip
 * virtualenv
 * memcached
 * libmemcached-dev
 * zlib
 * libxslt
 * libxml2
 * libbz2
 * uuid-dev
 * RabbitMQ
 * libreadline-dev (optional, but needed if you want readline support in the
   python interpreter)
 * libsqlite3-dev (required for SQLite)
 * libmysqlclient-dev and MySQLdb (required for MySQL)
 * libpq-dev and psycopg2 (required for PostgreSQL)

Packet list for Debian / Ubuntu::

    python-dev python-setuptools python-virtualenv mercurial subversion memcached libmemcached-dev build-essential zlib1g-dev libxml2-dev libxslt1-dev unzip libbz2-dev uuid-dev fabric libreadline-dev

If you want to use SQLite, add ``libsqlite3-dev``; for MySQL, add
``libmysqlclient-dev`` and ``python-mysqldb``; for PostgreSQL, you need
``libpq-dev`` and ``python-psycopg2``.

In addition, we need the dependencies for python-imaging::

    apt-get build-dep python-imaging

Now we can install Inyoka. But first we need to check out inyoka from the
mercurial repository. To do that we create a new folder ``inyoka-dev`` in your
projects directory and change into it. There we initialize the virtual
environment and check out Inyoka (main branch)::

    hg clone http://bitbucket.org/inyoka/inyoka-main/ inyoka

Or use the current experimental branch::

    hg clone http://bitbucket.org/EnTeQuAk/inyoka-sandbox/ inyoka

We're installing all of Inyoka's dependencies in a
`virtual environment <http://www.virtualenv.org/>`_ rather than globally for 
the whole system. This makes it possible to have different versions of those
libraries installed in one system, without affecting other applications.

To create the virtual environment, change to the root directory of the inyoka
repository and run::

    fab create_virtualenv

This will install the libraries in ``../inyoka-testsuite``, you may supply a
custom path (it is not required to create the target directory before)::

    fab create_virtualenv:directory=whereever/you/want

If your Linux distribution uses Python3 as default Python interpreter,
you need to use the ``interpreter`` parameter to enforce Python2.7::

    fab create_virtualenv:interpreter=python2.7

To specify both options, seperate them with a comma::

    fab create_virtualenv:directory=whereever/you/want,interpreter=python2.7

This will take quite a while, and a fast internet connection is recommended.
Note that the libraries are downloaded unencrypted and unsigned, so avoid
doing this in an unsafe network.

Every time we want to run inyoka, we need to activate the virtual environment,
so that the libraries we installed above are used, not the global ones
(you have to change the path if you specified a custom one before)::

    . ../inyoka-testsuite/bin/activate

(Do not forget the dot at the beginning!)

We are ready to run now.  If you start inyoka the first time (see below), a
default ``inyoka.ini`` will be created.  You can, of course, change settings as
you like.


AMQP Messaging and Celery
=========================

We're using celery to support cron-like tasks and delayed execution.  This
allows us to implement more features like never before and this
much easier.  See delayed "hotness" calculation for example that calculates
the hotness factor of various contents.

In order to use celery you need to setup a AMQP Server, we're using RabbitMQ
here for demonstration reasons.

If the server is not running already, you must start it; depending on your
configuration, it should be one of the following commands::

    invoke-rc.d rabbitmq-server start
    /etc/init.d/rabbitmq-server start
    service rabbitmq-server start

The server needs to be configured to create a new
namespace for inyoka to not disturb other services.

First we add a new user named ``inyoka`` with password ``default``::

    sudo rabbitmqctl add_user inyoka default

Right after that we add a new virtual host for inyoka::

    sudo rabbitmqctl add_vhost inyoka

Now we're more or less able to use that server.  But for development reasons
we need unlimited powers, as always.  So give the inyoka user all permissions
on the inyoka virtual host domain::

    sudo rabbitmqctl set_permissions -p inyoka inyoka ".*" ".*" ".*"

Now, use ``fab celeryd`` to start your celery server.


Database Initialization
=======================

SQLite is the default, so to use it you don't have to change anything.
You may define a custom database file name in ``inyoka.ini`` (create it if it
does not exist)::

    [database]
    url = sqlite://mydatabase.db

If you want to use MySQL or PostgreSQL, you need to make sure you have the
required libraries installed (see above).

Specify the database in ``inyoka.ini``::

    [database]
    url = (mysql|postgres)://user:password@host/database

Before starting we have to initialize the database::

    fab reset

This does also create test data.


.. _starting-the-server:

Starting the Server
===================

We need to configure the hostnames used by inyoka, so that your browser can
find it. Append the output of this command to the ``127.0.0.1`` line in your
``/etc/hosts``::

    fab lsdns

Now we can finally start the development server::

    fab runserver

Inyoka should be accessible at http://inyoka.local:5000/. Otherwise comment out the
IPv6 lines in your ``/etc/hosts`` and try again.


Additional setup
================

Below, there are some hints to make working with inyoka more comfortable,
although none of this is required to run it.

IPython
-------

IPython won't work in the virtual environment if you have installed it
globally, you have to install it separately in the virtualenv::

    pip install ipython

fab tab completion
------------------

There is a `bash tab completion for the fab command
<http://github.com/ricobl/dotfiles/blob/master/bin/fab_bash_completion>`_.
