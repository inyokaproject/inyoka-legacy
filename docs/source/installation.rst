============
Installation
============

Inyoka requires at least Python 2.6 to work correctly. Next to this Inyoka has
a lot of dependencies as well as a nice bootstrap process. This is documentated
on the following slides.

.. todo:

   This documentation is a bit distribution dependent, try to abstract it.

Dependencies and virtual environment
====================================

To get Inyoka work properly we need those dependencies (with headers):
 * Python (at least 2.6)
 * python-setuptools
 * mercurial
 * subversion
 * fabric
 * unzip
 * virtualenv
 * libmemcache
 * zlib
 * libxslt
 * libxml2
 * libbz2
 * libsqlite3-dev

For Ubuntu (or any Debian based distribution) use ``aptitude`` to install::

    aptitude install python-dev python-setuptools python-virtualenv mercurial subversion libmemcache-dev build-essential zlib1g-dev libxml2-dev libxslt1-dev unzip libbz2-dev libsqlite3-dev
    apt-get build-dep python-imaging

Because fabric is only in Ubuntu since Jaunty we use ``easy_install`` for it::

    easy_install fabric

Now we can install Inyoka. But first we need to check out inyoka from the
mercurial repository. To do that we create a new folder ``inyoka-dev`` in your
projects directory and change into it. There we initialize the virtual
environment and check out Inyoka (main branch)::

    hg clone http://bitbucket.org/inyoka/inyoka-main/ inyoka

Or use the current experimental branch::

    hg clone http://bitbucket.org/EnTeQuAk/inyoka-sandbox/ inyoka

Now it's possible to install the virtual environment. This is done with a simple
Python command::

    # assumed that you are located in the root directory of the inyoka repository
    fab create_virtualenv

Or create it under a user definied path::

    # it is not required to create the target directory before
    fab create_virtualenv:directory=../where-ever-you-want

We are ready to run now.  If you start inyoka the first time (see below) a
default `inyoka.ini` will be created.  You can, of course, create and modify
for you own purposes.


Database and other things
=========================

We are now ready to activate the virtual environment
(``../inyoka-testsuite`` is the default installation folder, may be replaced).
Do not forget the "." at the beginning!::

    . ../inyoka-testsuite/bin/activate

Before starting we have to initialize the database::

    fab initdb

And create some Test Data::

    fab reset

Last but not least make some DNS Setup in the ``/etc/hosts``::

    # put the output at the end of the 127.0.0.1 line
    fab lsdns

Now start the development server::

    fab runserver

Inyoka should accessible at http://inyoka.local:5000. Otherwise comment out the
IPv6 lines in your ``/etc/hosts`` and try again.

Almost done!

AMQP Messaging and Celery
=========================

We're using celery to support cron like tasks and delayed execution.  This
gives us the opportunity to implement more features like never before and this
much easier.  See delayed "hotness" calculation for example that calculates
the hotness factor of various contents.

In order to use celery you need to setup a AMQP Server, we're using RabbitMQ
here for demonstration reasons.

Install and start RabbitMQ::

    sudo apt-get install rabbitmq-server
    sudo /etc/init.d/rabbitmq-server start

The server now runs fine and only needs to be configured to create a new
namespace for inyoka to not disturb other services.

First we add a new user named ``inyoka`` with password ``default``::

    sudo rabbitmqctl add_user inyoka default

Right after that we add a new virtual host for inyoka::

    sudo rabbitmqctl add_vhost inyoka

Now we're more or less able to use that server.  But for development reasons
we need unlimited powers, as always.  So give the inyoka user all permissions
on the inyoka virtual host domain::

    sudo rabbitmqctl set_permissions -p inyoka inyoka ".*" ".*" ".*"

Now you can use ``fab celeryd`` to start your celery server.
