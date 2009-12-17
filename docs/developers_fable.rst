=================
Hacking on Inyoka
=================

Inyoka is written in Python and based on popular libraries.  The dynamic parts
in the user interface are created using HTML5 and jQuery.

This file should give you a brief overview how the code works and what
you should keep in mind working on it.

Please note that this file is work in progress.  Adapt it whenever you think
some urgent things needs to be written down so that other developers can use
them.  But try to keep it simple so that it's easy and fast to read.

If you want to know how to setup or use Inyoka see :doc:`installation` for more details.


Style Guide
~~~~~~~~~~~

All filenames have to be lowercase and ASCII only.

Python
------

Inyoka follows the PEP 8 for Python code.  The rule you should follow
is “adapt the code style used in the file”.  And that also means, put
whitespace where the original author put it and so on.

Indent with 4 *spaces* only.

Ordering of import statements is as defined in PEP 8, additionally:
 - Within the groups, `import …` statements stand above `from …` statements.
 - Within that, the statements are sorted alphabetically (shorter paths first).
 - Within `inyoka.*` imports, `inyoka.core` comes first, then `inyoka.utils`,
   then all other components (alphabetically)

No relative imports.

No imports from `inyoka.core.api` in core and utils (to avoid recursive imports)
(except middlewares)

JavaScript
----------

JavaScript code is intended with 2 spaces and *only two spaces*.

HTML
----

HTML code is also indented with 2 spaces.

**Every** page has to be valid `HTML 5 <http://www.whatwg.org/html5>`_

CSS
---

Indent your CSS 2.1 valid code with 4 spaces and adapt common formatting
styles.

URLs
~~~~

Rules for URLs are simple.  Services, e.g Ajax calls are prefixed with a underscore.
Use as less ids as possible and try to use "speeking" urls as much as possible.

Examples:

    /topic/new
    /topic/what-the-hack/edit
    /topic/what-the-hack/reply

    Ajax calls:

    /topic/_subscribe/what-the-hack
    /topic/_unsubscribe/what-the-hack


JavaScript Scripting
~~~~~~~~~~~~~~~~~~~~

All features that are implemented should work without JavaScript.
There must only be things implemented in JavaScript that could ease
some use-cases or shorten some workflow.  But everything else *must* work
without JavaScript.


Templates
~~~~~~~~~

Templates may not contain any CSS information besides classes.
Use classes as appropriate, and use as many of them as you like.
Keep them easy to read.

Use macros to ensure that you are using the same elements and
classes for the same widget (tags, users, badges etc.)


Unit Tests
~~~~~~~~~~

Inyoka uses `Nose <http://somethingaboutorange.com/mrl/projects/nose/0.11.1/>`_ for all
tests.  If you don't use functions or doctests you must inherit either
:class:`~inyoka.core.test.TestCase` for common unittests or
:class:`~inyoka.core.test.ViewTestCase` to test view functions.  See the 
:doc:`unittests` documentation for more details

Well, try to write the tests first, but we don't thrash you if you don't.
TDD is cool but not easy to use everywhere.  So our development cycle depends
on the hackers not on some kind of protocol nobody likes to use :)


Documentation
~~~~~~~~~~~~~

See :doc:`documentation` for details about how to document your work.
