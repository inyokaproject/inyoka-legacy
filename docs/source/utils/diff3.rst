================================
Inyoka Diff3 Algorithm Utilities
================================

.. automodule:: inyoka.utils.diff3


Utility Functions
=================

These functions are save to use as they only represent the algorithms
a in a more abstract way.

.. autofunction:: merge

.. autofunction:: stream_merge

.. autofunction:: get_close_matches

.. autofunction:: generate_udiff

.. autofunction:: prepare_udiff

.. autoclass:: DiffRenderer
    :members:

.. autoexception:: DiffConflict
    :members:


Inernal Matching Functions
==========================

These functions represent the underlying algorithm.  As this can change you
cannot rely on them.  So use them for reference but try to not overuse them!

.. autofunction:: tripple_match

.. autofunction:: match

.. autofunction:: find_match
