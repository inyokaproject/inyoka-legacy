=================
Hacking on Inyoka
=================

Inyoka is written in Python and based on popular libraries.  The dynamic parts
in the user interface are created using a subset of HTML5 and jQuery.

This file should give you a brief overview how the code works and what
you should keep in mind working on it.

.. note: This file is work in progress.  Adapt it whenever you think
         some urgent things needs to be written down so that other developers can use
         them.  But try to keep it simple so that it's easy and fast to read.

If you want to know how to setup or use Inyoka see :doc:`installation` for more details.


Style Guide
~~~~~~~~~~~

All filenames have to be lowercase and ASCII only.

Python
------

Inyoka follows the PEP 8 for Python code.  Next to that you should follow
“adapt the code style used in the file”.  And that also means, put
whitespace where the original author put it and so on.

Indent with 4 *spaces* only.

Ordering of import statements is as defined in PEP 8, additionally:
 - Within the groups, `import …` statements stand above `from …` statements.
 - Within that, the statements are sorted alphabetically (shorter paths first).
 - Within :mod:`inyoka.*` imports, :mod:`inyoka.core` comes first, then
   :mod:`inyoka.utils`, then all other components (alphabetically)
 - Use new language statemets instead of old backwards compatible statements,
   we require Python 2.6, so use at least the new `with` statement and the new
   `except Exception as err` instead of `except Exception, err`.

No relative imports.

No imports from :mod:`inyoka.core.api` in core and utils (to avoid recursive imports)
(except middlewares)

JavaScript
----------

JavaScript code is intended with 2 spaces and *only two spaces*.

HTML
----

HTML code is also indented with 2 spaces.

**Every** page has to be valid `HTML 5 <http://www.whatwg.org/html5>`_

If possible use a supported subset so do not use features not widely supported
by browsers.

CSS
---

Indent your CSS 2.1 valid code with 4 spaces and adapt common formatting
styles.

If widely supported you can use css3 features.


Naming Guide
~~~~~~~~~~~~

Besides the style there are some naming conventions we try to assert in our
internal modules.  These concern mostly our component system.

Interfaces
----------

An “interface” is a class that provides some general structure and does not
implement anything concrete.  An interface name must be prefixed with a
uppercased I.  Example::

    class IController(Interface):
        # ...

An interface generally inherits from :class:`~inyoka.Interface`.

Implementations
---------------

An “implementation” inherits an interface and implements concrete features.
They are generally named with Pythons PEP08 in mind::

    class NewsController(IController):
        # ...

Providers
----------

A “provider“ is commonly a small interface whose implementations are wrapped
within another component.  For example our admin interface is implemented with
the help of “providers”.  A small example::

    class IAdminProvider(Interface):
        name = None


    class ForumAdminProvider(IAdminProvider):
        # concrete implementation here...


    class IAdminController(IController):
        def get_endpoint_map(self):
            providers = ctx.get_component_instances(IAdminProvider)
            # ...

A provider interface inherits from :class:`inyoka.Interface` and follows it's
naming guides.

Controllers
-----------

As seen in the examples above we have “providers” whose implementations
are wrapped.  These wrappers are commonly called “controllers” because they
control other providers and control the concrete flow.

A controller interface inherits from :class:`inyoka.Interface` and follows it's
naming guides.  Besides that it should contain the name ``Controller`` to
specify that this is a special kind of interface.


URLs
~~~~

Rules for URLs are simple.  Use “speaking” names, use slugs to reference
contents instead of ids.  Services, e.g Ajax calls go to a special api
subdomain.  This will be done automatically if you use the
:class:`IServiceProvider` interface.

Examples:

    - http://forum.inyoka.local/topic/new
    - http://forum.inyoka.local/topic/what-the-hack/edit
    - http://forum.inyoka.local/topic/what-the-hack/reply

    Ajax calls:

    - http://api.inyoka.local/forum/topic/subscribe/what-the-hack
    - http://api.inyoka.local/forum/topic/unsubscribe/what-the-hack


JavaScript Scripting
~~~~~~~~~~~~~~~~~~~~

All features that are implemented should work without JavaScript.
There must only be things implemented in JavaScript that could ease
some use-cases or shorten some workflow.  But everything else *must* work
without JavaScript.

We are using extensively jQuery so use it wherever possible to ease the
development.  Note also that you should use only widely supported JavaScript
features, such as coroutines, workers and others are only supported in very
few browsers so do not use them!


Templates
~~~~~~~~~

Templates may not contain any CSS information besides classes and identifiers.
Use classes as appropriate, and use as many of them as you like.
Keep them easy to read.

Use macros to ensure that you are using the same elements and
classes for the same widget (tags, users, badges etc.)


Unit Tests
~~~~~~~~~~

Inyoka uses `Nose <http://somethingaboutorange.com/mrl/projects/nose/>`_ for all
tests.  If you don't use functions or doctests you must inherit either
:class:`~inyoka.core.test.TestSuite` for common unittests or
:class:`~inyoka.core.test.ViewTestSuite` to test view functions.  See the
:doc:`unittests` documentation for more details

Well, try to write the tests first, but we don't thrash you if you don't.
TDD is cool but not easy to use everywhere.  So our development cycle depends
on the hackers not on some kind of protocol nobody likes to use :)

But keep in mind that changing a lot of code is very much easier if you have
working unittests.  So please also check and debug your unittests if you're
not sure that they test what they should test.

As unittests often can be used as a reference about what's possible (as they
test all edge-cases) try to make them easy to read and document them as much
as possible.


Documentation
~~~~~~~~~~~~~

See :doc:`documentation` for details about how to document your work.
