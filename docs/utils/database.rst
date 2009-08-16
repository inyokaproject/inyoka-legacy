==================
Database Utilities
==================


.. automodule:: inyoka.utils.database


.. _database-usage:

Database Usage
==============

.. todo::

   write this section


.. _database-api:

Database API
============

.. data:: engine

    This object points to the current database engine.  The engine is the
    connection between SQLAlchemy and the DBAPI.  You may not need to
    use this object commonly.

.. data:: session

    This objects points to our scoped session.  It is used to hold our changes
    back until we ``flush`` those changes to the database.  It keeps track of
    our changes done to some objects and is our abstracted api to the database.

.. data:: db

    This is a virtual module holding all commonly used functions and classes we
    need to access the database, create new schemas and many more.

    In your daily work you mostly need the `db.session`.  All other classes
    are used usually in schema or mapper definitions.

    For more details about schema and mapper definitions see
    :ref:`database-usage`.
