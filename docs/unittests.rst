.. module:: inyoka.utils.test

===================
Unittests in Inyoka
===================

This document describes how the unittests work in Inyoka, how to write them
and how to use them.


What are unittests?
===================

…But first let's clearify what unittests are.  Unittests are some code pieces
that are used to create automated tests.  They ensure api and abi stability
and provide some easy to use test experience.

To write unittests is as easy to add new features to the code base.  But in
difference unittests are a lot more urgent than features.  And **Note** that
every new or changed code should have covered by a unittest.  This document
shows you how to create unittests, how to check for coverage and how to run
the final tests.


Test structure
==============

The inyoka unittests are located at the ``tests`` folder in the root of your
working copy.  Every application (forum, portal, wiki) and larger modules get
their own folder.  In this folder every file that should be recognized as a
test providing file shall start with ``test`` in the name.  In these files our
unittests are located.


How to test?
============

Before you can run the tests you need to setup your development environment.
Well, it's quite easy.  Just create a new database ``inyoka_test`` or set the
environment variable ``INYOKA_TEST_DATABASE`` to your choosen database name.
This database will be used to create all initial test data and provides the
testing interface for all database tests.

There are quite a bunch of unittests already existing.  Now you want to know
if inyoka behaves correct.  To run the unittests you need nothing more than
execute a ``make test``.  This imports `nosetest`_, builds a virtual testing
environment and creates all initial data needed to run the tests.

Once this is done our tests get collected and executed.  If one test fail
`nosetest`_ notices this, saves the traceback or whatever and continues with the
other tests.  At the very end you'll get an overview of all executed tests and
will see which failed.


Tell me how to write tests!
===========================

Okay… now we're finished with the basics.  Let's get to some more advanced
topic: How to write tests.

As I said above it's as easy as write other code.  So, let's open the file
``test_storage`` in the folder ``tests/utils``.  There are already quite a bunch of
unittests but we create our own.  Create a new function::

    def test_timeout():
        storage.set('foo', 'bar', 2)
        _compare('foo', 'bar')
        time.sleep(3)
        assert cache.get('foo') is None

This little function tests for a working cache-object timeout.  It covers the
very basics but shows how easy it is.


Advanced Stuff – View tests
===========================

Well, the unittests shown above are quite useful for testing utilities or
small code snippets.

There are serveral things to be able to test the inyoka views (e.g, :mod:`inyoka.portal.views`,
:mod:`ikhaya.forum.views`).  There is a function that can be used as a decorator
for small view tests and a :class:`unittest.TestCase` instance for more advanced tests.

This is how you can basicly test views (uses :func:`inyoka.test.view`)::

    @view('/', component='portal')
    def test_index(client, tctx, ctx):
        assert tctx['pm_count'] == 0


So now you need some code to set up some data, create other stuff.  What you
now can do is to use a :class:`inyoka.test.ViewTestCase`::

    class TestIndexView(ViewTestCase):
        component = 'portal'

        def setup(self):
            pass

        def test_pm_count(self):
            tctx = self.get_context('/')
            assert tctx['pm_count'] == 0


Testing API
===========

.. autoclass:: Context

   .. automethod:: add_forum(forum)


.. autoclass:: ViewTestCase

    .. automethod:: open_location(path, [method, options])

    .. automethod:: get_context(path, [method, options])


.. autofunction:: view([location, method, component, options])


.. _nosetest: http://somethingaboutorange.com/mrl/projects/nose/0.11.1/
