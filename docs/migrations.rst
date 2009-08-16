.. module:: inyoka.migrations

====================
Migrations In Inyoka
====================

This document describes how to write and use database migrations in Inyoka.

For more details see `SQLAlchemy-Migrate Documentation`_.

What Are Migrations?
====================

Migrations are a natural part of an application.  If you modify some code, add
new features or what ever you do – if there is a need to change the database
you need to get these changes applied everywhere Inyoka is deployed.

**Never forget to modify the schema in the inyoka application properly!**

Migration Structure
===================

All migrations are located in `inyoka.migrations.versions`.  They are named
according to a simple naming schema: ``$version_$description``.

.. _how-to-use-migrations:

How To Use Migrations
=====================

Using migrations is straightforward.  There is just one management-script for
all migration afairs, named ``dbmanage.py``.

**Initiate** your database schema::

    python dbmanage.py initial

**Upgrade** to the latest migration schema::

    python dbmanage.py upgrade

**Dowgrade** to a specific revision::

    python dbmanage.py downgrade 0

This erases all tables and data. The argument (zero in this example)
represents the migration stage.

**Show** the current migration version::

    python dbmanage.py version

**Create** a new change script::

    python dbmanage.py script "Add a new user table"

This creates an empty change script at
``inyoka/migrations/versions/002_Add_new_user_table.py`` (assuming that this is
our second migration)


Write Migrations
================

Now you :ref:`learned <how-to-use-migrations>` how to use and create migration
scripts.  In this chapther we will show you how to write new migrations.

For this example we assume that we need to set more informations on the user
profiles.  Let's say we build a new generic user-information system.  We do
not cover application code here, but only the neccessary steps to migrate the
database structure.

First we create a new change script::

    python dbmanage.py script "Create A New User Information Table"

Then we can open it (located in ``inyoka/migrations/versions``) and edit it.
Please note that we must not use the Inyoka database engine but the
sqlalchemy-migrate one.  But I'll cover that later.

First, we define the required metadata, user table and user-profile table::

    user_table = Table('portal_user', metadata, autoload=True)

    user_profile_table = Table('portal_user_profile', metadata,
        Column('id', Integer, primary_key=True),
        Column('user_id', Integer, ForeignKey('portal_user.id')),
        Column('jabber', String(200)),
        Column('icq', String(16)),
        Column('msn', String(200)),
        Column('aim', String(200)),
        Column('yim', String(200)),
        Column('skype', String(200)),
        Column('wengophone', String(200)),
        Column('sip', String(200)),
        Column('signature', Text),
        Column('coordinates_long', Float),
        Column('coordinates_lat', Float),
        Column('location', String(200)),
        Column('gpgkey', String(8)),
        Column('occupation', String(200)),
        Column('interests', String(200)),
        Column('website', String(200)),
        Column('launchpad', String(50)),
    )

And after we defined them we need to create the upgrade action.  Update your
**upgrade** function with the following code::


    def upgrade():
        # create the table
        metadata.create_all([user_profile_table])

        # collect the columns and user ids
        user_ids = (x[0] for x in engine.execute(select([user_table.c.id])))
        columns = ('jabber', 'icq', 'msn', 'aim', 'yim', 'skype', 'wengophone',
                   'sip', 'signature', 'coordinates_long', 'coordinates_lat',
                   'location', 'gpgkey', 'occupation', 'interests', 'website',
                   'launchpad')
        cols = [user_table.c.get(x) for x in columns]

        # move the values into the new table
        for uid in user_ids:
            u = [x[0] for x in engine.execute(select(cols) \
                                     .where(user_table.c.id == uid)) \
                                     .fetchall()]
            values = dict(zip(columns, u))
            values['user_id'] = uid
            engine.execute(user_profile_table.insert(values=values))

        # ...and drop the old columns
        for column in cols:
            user_table.drop_column(column)

        session.commit()

Now all data is transfered and old data is dropped.


Migration API
=============

.. autofunction:: _set_storage(values)


.. _`SQLAlchemy-Migrate Documentation`: http://packages.python.org/sqlalchemy-migrate/
