============
Installation
============

Inyoka requires at least Python 2.5 to work correctly. Next to this Inyoka has
a lot of dependencies as well as a nice bootstrap process. This is documentated
on the following slides.


Dependencies and virtual environment
====================================

To get Inyoka work properly we need those dependencies:
* Python (at least 2.5)
* python-setuptools
* mercurial
* fabric

For Ubuntu (or any Debian based distribution) use ``aptitude`` to install::

    aptitude install python-dev python-setuptools python-virtualenv mercurial

Because fabric is only in Ubuntu since Jaunty we use ``easy_install`` for it::

    easy_install fabric

Now we can install Inyoka. But first we need to check out inyoka from the
mercurial repository. To do that we create a new folder ``inyoka-dev`` in your
projects directory and change into it. There we initialize the virtual
environment and check out Inyoka (main branch)::

    hg clone http://bitbucket.org/inyoka/inyoka-main/ inyoka

Or use the current experimental branch::

    hg clone http://bitbucket.org/EnTeQuAk/inyoka-sandbox/ inyoka

Right before we can initialize the virtual environment we need to install some
development packages.

For Ubuntu again ``aptitude`` (as root)::

    sudo aptitude install libmemcache-dev build-essential zlib1g-dev
    apt-get build-dep python-imaging

Now it's possible to install the virtual environment. This is done with a simple
Python command::

    # assumed that you are located in inyoka-dev/inyoka
    python extra/make-bootstrap.py > ../bootstrap.py
    cd ..
    # make sure that the virtualenv is not activated. If yes, execute `deactivate`
    python bootstrap.py .

We are ready to run now.  If you start inyoka the first time (see below) a
default `inyoka.ini` will be created.  You can, of course, create and modify
for you own purposes.


Database and other things
=========================

We are now ready to enter the virtual environment (assumed you are located in
``inyoka-dev/inyoka``)::

    . ../bin/activate
    
Before starting we have to initialize the database::

    fab initdb

Now start the development server::

    fab runserver

Ready!
