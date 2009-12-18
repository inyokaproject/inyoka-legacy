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


How to write unittests
======================

This part shall give you some example of how to write unittest.

There are various types of how to write unittests.  There are function tests,
test suites and test cases.  All of them have different purposes and
implementations.

Function Tests
--------------
Function tests for example are just functions acting with
:mod:`nose.tools` and running their tests in the function body.

Exmaple::

    def test_bidimap():
        map = BidiMap({
            1: 'dump',
            2: 'smartly',
            3: 'clever'
        })
        eq_(map[1], 'dump')
        eq_(map[2], 'smartly')
        eq_(map[3], 'clever')
        # and reversed
        eq_(map['dump'], 1)
        eq_(map['smartly'], 2)
        eq_(map['clever'], 3)

Now this function is just called and the return values or exceptions are
tracked.  It's the easiest way to write unittests.  See the Nose
documentations for more details.

Test Suites
-----------
A :class:`TestSuite` is the most common implementation in the Inyoka test
framework.  They are similar to test cases but have some fixture framework
integrated.  Let the code speak::

    class TestEntryModel(TestSuite):

        fixtures = {
            'entry': fixture(Entry, code=u'void', title=u'some paste')
        }

        @with_fixtures('entry')
        def test_entry(self, fixtures):
            entry = fixtures['entry']
            eq_(entry.code, u'void')

This is only a very simple example.  As you see a method can load fixtures
with the `with_fixture` decorator.  Only those get loaded!

All loaded models are stored in a dictionary that is applied to the test
method, here named `fixtures`.

Let's see a more advanced example::

    def get_data_callback(title=None):
        def callback():
            data = {
                'author': User.query.get('anonymous'),
                'code': 'void'
            }
            if title is not None:
                data['title'] = title
            return data
        return callback


    class TestEntryModel(TestSuite):

        fixtures = {
            'pastes': [
                fixture(Entry, get_data_callback(u'some paste')),
                fixture(Entry, get_data_callback()),
        ]}

        @with_fixtures('pastes')
        def test_display_title(self, fixtures):
            e1, e2 = fixtures['pastes']
            eq_(e1.display_title, 'some paste')
            eq_(e2.display_title, '#%d' % e2.id)
            eq_(unicode(e1), 'some paste')
            eq_(unicode(e2), '#%d' % e2.id)


Yea, this is heavy, isn't it?  But it's as simple as it looks like… All
fixtures in the `fixtures` dictionary of the :class:`TestSuite` are loaded if
specified by `with_fixtures`.  As such there are two models loaded.  The
callback is just another method to apply data to the model.  It's commonly
used if you have to query database since we cannot do that in the class body.


Unittest Helpers
================

Decorators
----------

.. autofunction:: fixture

.. autofunction:: future

.. autofunction:: with_fixtures


Test Cases
----------

.. autoclass:: TestSuite
   :members:

.. autoclass:: ViewTestSuite
   :members:


Other Stuff
-----------

.. autoclass:: InyokaPlugin
   :members:

.. autoclass:: TestResponse
   :members:
