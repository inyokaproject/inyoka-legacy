.. module:: inyoka

=======================
Inyoka Component System
=======================

Inyoka is based on a object oriented component system that is used to
integrate services, controllers, models and other stuff.

This system is based on one class, :class:`Component` that is used to keep track
of so called “interfaces”.  A component describes some API and implements
basic functions that are commonly used on similar components.  Components are
commonly named with a leading “I”.  E.g “IAttachmentProvider”, “IMiddleware”.

An “implementation” that implements the components API and functions needs to
subclass the implemented component.

Example Usage
-------------

.. sourcecode:: pycon

    >>> class IAttachmentProvider(Component):
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
    >>> IAttachmentProvider.get_component_classes()
    []
    # now we setup those components.  The empty list tells the function
    # that it only has to setup already known components.
    >>> setup_components([])
    ...
    >>> IAttachmentProvider.get_component_classes()
    [<class '__main__.NonBoundAttachmentProvider'>, <class '__main__.ForumPostAttachmentProvider'>]

As you see you need to setup the component system before using it.

Component Interfaces
--------------------

.. autoclass:: Component

.. autofunction:: setup_components
