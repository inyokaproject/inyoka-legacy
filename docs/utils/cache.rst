===================
Inyoka Cache System
===================

.. automodule:: inyoka.utils.cache

.. data:: cache

   This object represents the current active cache instance.
   Import this object is commonly enough for use the cache
   system.  It defaults to either a memcached system or a
   in memory system depending on the existense of
   :confval:`MEMCACHE_SERVERS`. 


.. _cache-usage:

Cache System Usage
==================

The cache system has a similar api as a `dict` type.

To cache an object you use :meth:`cache.set`:

.. sourcecode:: pycon

   >>> cache.set('foo', 'some object') 

Now we query this object again:

.. sourcecode:: pycon

    >>> cache.get('foo')
    'some object'

This are the very basic options.  You can use :meth:`cache.set_many` and
:meth:`cache.get_many` if you need to cache or query more then one object.

For more details see `The Werkzeug documentation
<http://werkzeug.pocoo.org/documentation/contrib/cache>`_

.. _cache-api:

Cache System API
================

.. autoclass:: InyokaMemcachedCache
   :members: get


.. autofunction:: set_real_cache

.. autofunction:: set_test_cache
