==================
Documenting Inyoka
==================

We use a library called `Sphinx <http://sphinx.pocoo.org>`_ to create the 
documentation of Inyoka. The original text will is based in the docs directory
or directly in the source code. Sphinx is capable to translate this into 
different formats like html or latex. We will describe at the beginning how to
create a html-documentation from the existing code. In the following we 
introduce rapidely some very basic concepts for in code documentation and for 
writing documents. For more informations you can read the great 
`introduction into Sphinx on its website <http://sphinx.pocoo.org/contents.html>`_ .

Build a standard html documentation
===================================

In the following we suppose that you activated the virtual environment (see 
:doc:`installation`) and that you are in the ``inyoka/docs`` directory. Now you
can run::

    sphinx-build -b html . build/

The complete documentation is now located in ``build`` and it can be opened with
the browser of your choice.

Write documentation in the source code
======================================

The for moduls, classes, methods and functions is simply done in the according 
docstring. The mark-up syntax is completly documented on the `Sphinx website 
<http://sphinx.pocoo.org/contents.html>`_. 

Write documentation in extra files
==================================

Sometimes you want to describe things that don't belong in the code itself (like
this section you are reading now). Thatfore you have the possibility to create
extra files. Those files have to be located into the ``docs`` folder and of the
**.rst** format. Please don't forget to add them to the *index.rst* otherwise it 
will be hard to find it for the user.
