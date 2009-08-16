.. module:: inyoka

====================================
Welcome To The Inyoka Documentation!
====================================

Contents
========

The following applications are part of inyoka so far:

:doc:`portal/index`
    The index application.  On no subdomain and the portal page.
    Aggregates recent ikhaya posts and similar stuff.  Also shows the
    number of online users.

:doc:`forum/index`
    The forum component.  It's inspired by phpBB2 which was previously
    used on the German ubuntuusers.de webpage.  Some of the functionallity
    was extended over time though.  Especially an improved notification
    system, attachments and subforums (latter new in inyoka)

:doc:`wiki/index`
    Moin inspired wiki engine.  It's not yet as advanced as moin 1.7 but
    has revisioned pages a better parser which can savely generate docbook
    and other XML based output formats.  The wiki parser also has some
    BBCode elements for compatibility with the old phpBB syntax and is
    used in other components (`forum`, `ikhaya`, ...) as well.

:doc:`planet/index`
    A planet planet like feed aggregator.  It has archives and santized
    input data thanks to feedparser.

:doc:`ikhaya/index`
    Ikhaya is zulu for `home` and a blog application.  It's used on the
    German ubuntuusers portal for site wide annoucements and other news.
    It doesn't show up on the planet automatically, for that you have to
    add the ikhaya feed to it like for any other blog too

:doc:`pastebin/index`
    A pastebin that uses Pygments for highlighting.  It does not support
    diffing yet but allows to download pastes.


Inyoka Basics
-------------

This section covers the very basics of inyoka.

.. toctree::
    :maxdepth: 2

    installation
    migrations


Utilities
---------

This section covers all utilities inyoka implements.

.. toctree::
    :maxdepth: 2

    utils/cache
    utils/captcha
    utils/collections
    utils/database

References
----------

.. toctree::
    :maxdepth: 2

    unittests


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. Note:
    Do not remote this line. It prevents us from serveral warnings!
    These files are indexed on another way than a toctree, so we need
    to reference them here so that sphinx is happy again :)
    
.. toctree::
   :hidden:

   forum/index
   ikhaya/index
   pastebin/index
   planet/index
   portal/index
   wiki/index
