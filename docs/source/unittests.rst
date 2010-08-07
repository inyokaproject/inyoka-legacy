.. module:: inyoka.core.test

===================
Unittests in Inyoka
===================

This document describes how unittests work in Inyoka, how to write them
and how to use them more effectively.


What are unittests?
===================

First let's clearify what unittests are.  Unittests are some code pieces
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
assumed in :doc:`installation`) and type in ``fab test``.


How to write unittests
======================

This part shall give you some example of how to write unittests.

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


Test Cases
-----------

In the inyoka test framework there are various test case implementations.  The
most common is the :class:`TestCase`, it's more or less the same as
`unittest.TestCase` so use it that way::

    class TestOrderedDict(TestCase):

        def test_dict_inheritance(self):
            d = OrderedDict()
            self.assertTrue(isinstance(d, dict))

        def test_various_initialisation_features(self):
            assert_raises(TypeError, OrderedDict, 1, 3)

        def test_clear(self):
            d = OrderedDict([('a', 1), ('b', 2), ('c', 3), ('d', 4)])
            d.clear()
            assert_false('a' in d)
            assert_false('b' in d)


Next to that there's the :class:`DatabaseTestCase`.

This class allows you to use fixtures.  So, what are fixtures?  Did you ever
have to write initalisation code for unittests with database models with their
references and ids and so much other stuff.  You don't have to do that
anymore, mostly.

I give you a short example::

    class TestEntryModel(DatabaseTestCase):

        fixtures = [
            {Entry: [{'code': u'void', 'title': u'some paste'}]},
        ]

        def test_entry(self):
            entry = self.data['Entry'][0]
            eq_(entry.code, u'void')

I guess the code speaks for itself.  But let me explain that a bit.  You
define a list of fixtures, dictionaries.  Every dictionary has as it's key the
model class that needs to be initialized.  As for the value there is a list of
more dictionaries with the attributes to initialize the model with.

So this example creates that: ``Entry(code=u'void', title=u'some paste')``.
Easy isn't it?  All those fixtures are registered in a class attribute called
`data`.  It's a dictionary with the exact model names as key and the list of
objects as values.  So it looks like this::

    data = {'Entry': [Entry(code=u'void', title=u'some paste')]}

Okay, I mentioned references, ids and all that difficult stuff.  Now an
advanced example::

    class TestNewsModels(DatabaseTestCase):

        fixtures = [{
            User: [
                {'&bob': {'username': u'Bob', 'email': u'bob@noone.com'}},
                {'&peter': {'username': u'Peter', 'email': u'peter@noo.com'}}
            ]}, {
            Tag: [
                {'&ubuntu': {'name': u'Ubuntu'}},
                {'&ubuntuusers': {'name': u'Ubuntuusers'}}
            ]}, {
            Article: [
                {'&rocks_article': {
                    'title': u'My Ubuntu rocks!!',
                    'intro': u'Well, it just rocks!!',
                    'text': u'And because you\'re so tschaka baam, you\'re using Ubuntu!!',
                    'public': 'Y',
                    'tags': ['*ubuntu'],
                    'author': '*bob'
                }}
            ]}, {
            Comment: [{'text': u'Bah, cool article!', 'author': '*bob', 'article': '*rocks_article'},
                        {'text': u'This article sucks!', 'author': '*bob', 'article': '*rocks_article'}]
        }]

        def test_article_attributes(self):
            article = self.data['Article'][0]
            eq_(article.slug, 'my-ubuntu-rocks')

        def test_comment_counter(self):
            article = self.data['Article'][0]
            eq_(article.comment_count, 2)

        def test_article_automatic_updated_pub_date(self):
            article = self.data['Article'][0]
            eq_(article.was_updated, False)
            article.updated = article.pub_date + datetime.timedelta(days=2)
            db.session.commit()
            eq_(article.was_updated, True)


Confused?  I hope not, but it's as easy as the previous example.  The only
difference is that you can now see how you define references and links to
those references.

But let's go on slowly.

.. code-block:: python

    {User: [
        {'&bob': {'username': u'Bob', 'email': u'bob@noone.com'}},
    ]}

This just defines a new `User` object with the username `Bob` and the email
`bob@noone.com`.  That `&bob` key at the front just registers internal that
here's a reference named `bob` that points exactly to that instance.

Take this:

.. code-block:: python

    {Article: [
        {'&rocks_article': {
            'title': u'My Ubuntu rocks!!',
            'intro': u'Well, it just rocks!!',
            'text': u'And because you\'re so tschaka baam, you\'re using Ubuntu!!',
            'public': 'Y',
            'tags': ['*ubuntu'],
            'author': '*bob'
        }}
    ]}


This too registers a new reference called `rocks_article`.  But do you see the
values with the star in it?  That are links to references!  The fixture system
converst that into this call:

.. code-block:: python

    bob = User(username=u'Bob', 'email', u'bob@noone.com')

    data['Article'] = [Article(title=u'My Ubuntu rocks!!',
                          intro=u'Well, it just rocks!!',
                          text=u'And because you\'re so tschaka baam, you\'re using Ubuntu!!',
                          public=True,
                          author=bob)]

Of course the `bob` object is created much earlier.  But you can see another
speciality in here, see the `public` attribute.  It was converted from `Y` to
`True`.  The reversed way would be from `N` to `False`, cool isn't it?

If you have any further questions you may have a look at already
existing unittests as they use the fixture system quite often.


Implement models in unittests
-----------------------------

Sometimes it's required to implement your own models in unittests to ensure
you rely on an interface that's not going to change, or to add some
mocking-features required to properly test your functions.

The way you implement models is the same as you do by writing applications.
You inherit from :class:`~inyoka.core.database.Model` or write tables by using
:class:`~inyoka.core.database.Table`.  To register those models use the
:class:`inyoka.core.test.TestResourceManager`.  See it's docstring for more
examples.



Unittest Helpers
================

Decorators
----------

.. autofunction:: future

.. autofunction:: with_fixtures

.. autofunction:: refresh_database


Test Cases
----------

.. autoclass:: TestCase
   :members:

.. autoclass:: DatabaseTestCase
   :members:

.. autoclass:: ViewTestCase
   :members:

.. autoclass:: TestResourceManager
   :members:

.. autoclass:: FixtureLoader
   :members:


Other Stuff
-----------

.. autoclass:: InyokaPlugin
   :members:

.. autoclass:: TestResponse
   :members:
