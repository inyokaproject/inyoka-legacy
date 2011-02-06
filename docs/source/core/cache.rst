cache Package
=============

.. automodule:: inyoka.core.cache

Configuring the Cache
---------------------

The following configuration values exist for the caching system:

.. tabularcolumns:: |p{6.5cm}|p{8.5cm}|


=============================== =========================================
``caching.system``              Specifies which cache system to use.

                                Built-in cache types:

                                * **null**: NullCache
                                * **simple**: SimpleCache
                                * **memcached**: MemcachedCache
                                * **gaememcached**: GAEMemcachedCache
                                * **filesystem**: FileSystemCache
                                * **database**: DatabaseCache

``caching.filesystem_path``     The path for filesystem caches.
``caching.timeout``             The default timeout that is used if no
                                timeout is specified. Unit of time is
                                seconds.
``caching.memcached_servers``   A list or a tuple of server addresses.
                                Used only for MemcachedCache
=============================== =========================================

Caching Functions
-----------------

To cache functions you will use the :meth:`~cached` decorator.
This decorator will use request.path by default for the cache_key.::

    @cached(timeout=50, key_prefix='all_comments')
    def get_all_comments():
        comments = do_serious_dbio()
        return [x.author for x in comments]

    cached_comments = get_all_comments()

The cached decorator has another optional argument called ``unless``. This
argument accepts a callable that returns True or False. If ``unless`` returns
``True`` then it will bypass the caching mechanism entirely. The default
configuration uses ``request.path`` to seperate between various caches.

Using the same ``@cached`` decorator you are also able to cache the result of other
non-request related functions. The only stipulation is that you replace the
``key_prefix``, otherwise it will use the request.path cache_key.::

    @cached(timeout=50, key_prefix='all_comments')
    def get_all_comments():
        comments = do_serious_dbio()
        return [x.author for x in comments]

    cached_comments = get_all_comments()

Memoization
-----------

See :meth:`~memoize`

In memoization, the functions arguments are also included into the cache_key.

.. note::

	With functions that do not receive arguments, :meth:`~cached` and
	:meth:`~memoize` are effectively the same.
	
Memoize is also designed for instance objects, since it will take into account
that functions id. The theory here is that if you have a function you need
to call several times in one request, it would only be calculated the first
time that function is called with those arguments. For example, an sqlalchemy
object that determines if a user has a role. You might need to call this
function many times during a single request.::

	class User(db.Model):
		@memoize(50)
		def has_membership(role):
			return self.groups.filter_by(role=role).count() >= 1
			
		
Deleting memoize cache
``````````````````````

You might need to delete the cache on a per-function bases. Using the above
example, lets say you change the users permissions and assign them to a role,
but now you need to re-calculate if they have certain memberships or not.
You can do this with the :meth:`~clear_memoized` function.::

	clear_memoized('has_membership')
	
.. note::

	You can pass as many function names as you wish to delete_memoized.


API
---

.. autodata:: cache

.. autofunction:: cached
.. autofunction:: memoize
.. autofunction:: clear_memoized
.. autoclass:: DatabaseCache
    :members:
.. autofunction:: set_cache
