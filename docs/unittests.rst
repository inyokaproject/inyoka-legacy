.. module:: inyoka.core.test

===================
Unittests in Inyoka
===================

This document describes how the unittests work in Inyoka, how to write them
and how to use them.


What are unittests?
===================

…But first let's clearify what unittests are.  Unittests are some code pieces
that are used to create automated tests.  They ensure API and ABI stability and
provide some easy to use test experience.

To write unittests is as easy to add new features to the code base.  But in
difference unittests are a lot more urgent than features.  And **note** that
every new or changed code should be covered by a unittest.  This document shows
you how to create unittests, how to check for coverage and how to run the final
tests.


Test structure
==============

The inyoka unittests are located at the ``tests`` folder in the root of your
working copy.  Every application (forum, portal, wiki) and larger modules get
their own folder.  In this folder every file that should be recognized as a test
providing file shall start with ``test`` in the name.  In these files our
unittests are located.


Run the unittests
=================

To run the unittests just go to the root inyoka folder (`inyoka-dev` as
assumed in :doc:`installation`) and type in ``make test``.


Unittest Helpers
================

Decorators
----------

.. autofunction:: fixture

.. autofunction:: future

.. autofunction:: with_fixtures


Test Cases
----------

.. autoclass:: ViewTestCase
   :members:


Other Stuff
-----------

.. autoclass:: InyokaPlugin
   :members:

.. autoclass:: TestResponse
   :members:
