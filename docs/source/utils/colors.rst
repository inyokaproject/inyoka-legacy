===================================
Inyoka Command Line Color Utilities
===================================

.. automodule:: inyoka.utils.colors

Helpers
=======

.. autofunction:: nocolor

.. autofunction:: reset_color

.. autofunction:: colorize


Colorizing Functions
--------------------

To use the functions just import the function naming the color you want to use
to format your text.  E.g:

.. sourcecode:: pycon

    >>> from inyoka.utils.colors import bold
    >>> bold("Something ugly")
    '\x1b[01mSomething ugly\x1b[39;49;00m'

Supported colors are: ``teal``, ``turquoise``, ``darkteal``,
``fuscia``, ``fuchsia``, ``purple``, ``blue``, ``darkblue``,
``green``, ``darkgreen``, ``yellow``, ``brown``, ``darkyellow``,
``red``, ``darkred`` and ``white``

Besides those you can use ``bold`` and ``underline`` for more advanced formating.
