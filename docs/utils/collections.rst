===========
Collections
===========

.. automodule:: inyoka.utils.collections


.. _collections-api:

Collections API
===============

.. autoclass:: MultiMap
    :members:

    A :class:`MultiMap` implements the full `dict` signature.

    .. note::

        Instances of :class:`MultiMap` are immutable.  So only use them to
        represent data, not to modify it.

    Some usage examples:

    .. sourcecode:: pycon

        # initiate a multi map.
        >>> map = MultiMap([('foo', 1), ('foo', 2), ('baaaz', 1), ('baaaz', 2)])
        # show all existing keys.  Note that you can only have a key one time,
        # as in pythons dict type.
        >>> map.keys()
        ['baaaz', 'foo']
        # and query all items, mapped to the key.  As you see you get multiple
        # values for one key.
        >>> map.items()
        [('baaaz', [1, 2]), ('foo', [1, 2])]
        >>> map.values()
        [[1, 2], [1, 2]]
        >>> map.clear()
        >>> map
        MultiMap([])
        # MultiMap instances are immutable.
        >>> map.pop()
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
          File "inyoka/utils/collections.py", line 38, in _immutable
            self.__class__.__name__)
        TypeError: 'MultiMap' instances are immutable 
