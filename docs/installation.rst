============
Installation
============

Inyoka requires at least Python 2.5 to work correctly. Next to this Inyoka has
a lot of dependencies as well as a nice bootstrap process. This is documentated
on the following slides.

Dependencies and virtual environment
====================================

To get Inyoka work properly we need those dependencies: MySQL-Server, Python (at least 2.5) as well as python-setuptools and mercurial.

For Ubuntu (or any Debian based distribution) use ``aptitude`` to install::

    aptitude install mysql-server python-dev python-setuptools python-virtualenv mercurial subversion

If you use Fedora use ``yum`` for the installation process::

    yum install mysql-server python-devel python-setuptools python-setuptools-devel python-virtualenv mercurial

Now we can install Inyoka. But first we need to checkout inyoka from the mercurial repository. To do that we create a new folder ``ubuntuusers`` in our projects directory. There we initialize the virtual environment and checkout Inyoka (SQLAlchemy branch)::

    hg clone http://hg.ubuntu-eu.org/ubuntu-de-inyoka_sa inyoka

Right before we can initialize the virtual environment we need to install some development packages.

For Ubuntu again ``aptitude`` (as root)::

    aptitude install libmemcache-dev libxapian-dev build-essential zlib1g-dev
    apt-get build-dep python-mysqldb python-imaging

And for Fedora with ``yum`` (as root)::

    yum install memcached xapian-core-devel gcc zlib-devel
    yum-builddep python-imaging MySQL-python

Now it's possible to install the virtual environment. This is done with a simple python command::

    # required that you are located in ubuntuusers/inyoka
    python make-bootstrap.py > ../bootstrap.py
    cd ..
    # make sure that the virtualenv is not activated. If yes, execute `deactivate`
    python bootstrap.py .


Well, this takes some time which needs to be used useful. So we create a file ``DJANGO_SETTINGS_MODULE`` in the inyoka root directory (``ubuntuusers/inyoka`` in this example)::

    echo "development_settings" > DJANGO_SETTINGS_MODULE

We are not ready yet. To get inyoka ready we need to create this settings moule. Do do that copy the existing ``example_development_settings.py`` to ``development_settings.py``::
    
    cp example_development_settings.py development_settings.py

You can now modify the ``development_settings.py`` for your own purposes if you like.

Database and other things
=========================

We are now ready to enter the virtual environment (assumed we are located in ``ubuntuusers/inyoka``) and set the required environment variables (source init.sh)::

    . ../bin/activate
    . init.sh


To get the database ready we need to run migrate (see `inyoka.migrations` for more details), create a super user and our test data::

    python dbmanage.py initial
    make test_data
    python manage-inyoka.py create_superuser

Now start the development server::

    make server

Ready!

It's required to append some entries to the ``/etc/hosts`` file to access the server locally. Modify your hosts file to match the following::

   127.0.0.1 localhost.localdomain localhost ubuntuusers.local admin.ubuntuusers.local forum.ubuntuusers.local paste.ubuntuusers.local wiki.ubuntuusers.local planet.ubuntuusers.local ikhaya.ubuntuusers.local static.ubuntuusers.local media.ubuntuusers.local
