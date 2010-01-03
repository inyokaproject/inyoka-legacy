.. module:: inyoka

=======================
Inyoka Component System
=======================

Inyoka is based on a object oriented component system that is used to
integrate services, controllers, models and other stuff.

This system is based on one class, :class:`Interface` that is used to keep track
of so called “interfaces”.  A interface describes some API and implements
basic functions that are commonly used on similar components.  Interfaces are
commonly named with a leading “I”.  E.g “IAttachmentProvider”, “IMiddleware”.

An “implementation” that implements the components API and functions needs to
subclass the implemented interface.

Example Usage
-------------

.. sourcecode:: pycon

    >>> class IAttachmentProvider(Interface):
    ...     def get_id(self):
    ...         raise NotImplementedError()
    ...
    >>> class NonBoundAttachmentProvider(IAttachmentProvider):
    ...     def get_id(self):
    ...         return 'non_bound'
    ...
    >>> class ForumPostAttachmentProvider(IAttachmentProvider):
    ...     def get_id(self):
    ...         return 'forum_post'
    ...
    >>> from inyoka.core.api import ctx
    >>> ctx.get_implementations(IAttachmentProvider)
    []
    # now we setup those components.  The empty list tells the function
    # that it only has to setup already known components.
    >>> ctx.load_components([NonBoundAttachmentProvider, ForumPostAttachmentProvider])
    ...
    >>> ctx.get_implementations(IAttachmentProvider)
    [<class '__main__.NonBoundAttachmentProvider'>, <class '__main__.ForumPostAttachmentProvider'>]

As you see you need to setup the component system before using it.

Component Interfaces
--------------------

.. autoclass:: Interface
   :members:

.. autoclass:: ApplicationContext

    .. attribute:: dispatcher

       The WSGI dispatcher.  It's an instance of
       :class:`~inyoka.dispatcher.RequestDispatcher`.

    .. attribute:: current_request

       A property pointing to the current active request
       in the thread-local.

    .. automethod:: load_component

    .. automethod:: load_components

    .. automethod:: unload_components

    .. automethod:: load_packages

    .. automethod:: get_implementations

    .. automethod:: get_instance
