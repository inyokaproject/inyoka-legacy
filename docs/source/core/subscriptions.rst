====================
The Subscription API
====================

Subscriptions are a way for a user to keep himself informed about new objects
such as a new topic in a forum where he wants to help others, a new news entry
in a category he likes, or (for moderators) a new reported topic.

There are two basic ways to be informed of a new object: The first one is
receiving messages, either an email or via jabber. The second one is by
looking at the list of new objects on the website (referred to as ”the
list” below)

Terminology and Internal Functioning
====================================

There are lots of different subscription **type**\s. For example, this may be
“topics in a given forum” or “comments on a news entry”. These are
implemented by subclassing :class:`SubscriptionType` (see
:ref:`defining-subscription-types` below).

A **subject** is some item a user can subscribe to; an **object** is an item
within a subject, for example for the “topics in a forum“ type the forum is
the subject, and the topics in this forum are the corresponding objects.

For this purpose, each subscription type defines one object type and one
subject type. For example the subject type of the “topics in a forum” type is
:class:`Forum`, its object type is :class:`Topic`. The subject type may be None
however: This means that the user can only subscribe to this subscription type
as a whole, in other words there are not several subjects to subscribe to. This
is for example useful to allow subscribing to the news platform as a whole (and
not just a single category) or for reported topics.

Each subscription type is associated with several **action**\s. An action is
something that can happen to the object. For example for the “topics in a
forum” type, actions could be “new topic in given forum” or “topic moved to
given forum”. Note the difference: A type defines the relation between object
and subject, the action is the formation of that relation.

There are two basic **mode**\s how a subscription can work. Each subscription
type uses one of theses modes:
 * For example there are posts in a topic or comments on a blog entry: They are
   presented in a consecutive manner, the user can (which is the important
   point for the way subscriptions work) simply read on with the next object
   after having read one. So the user is only notified for the first new object
   for each subscription, then he does not receive further messages until he
   has read it. In the list, not every new object is mentioned and linked to,
   but just the first one that the user has not yet read.
   We call this mode **sequent**. 
 * Then there is the other case, where the objects are not really related to
   each other, the important point for us here is that they are not presented
   in order, meaning the user can and will *not* read on with another one.
   Examples are topics in a forum or blog entries. This means that the user
   receives a message for each new object, and in the list, there is an entry
   for each new object. This mode is called **multiple**.

Each subscription (means: each instance of the
:class:`~inyoka.core.subscriptions.models.Subscription` model) represents a
*user* subscribed to a *subject* of some *type*, and contains some additional
attributes that are needed to create the list of new objects and to not send
messages when not necessary:
 * The **count** of unread objects. This is only vital for the sequent mode,
   where it controls whether to send out a message or not; in multiple mode it
   is just used to allow displaying a number of unread objects.
 * For sequent types: The **first unread object**. This is the one the message
   is sent out for and is used to allow linking directly to it in the list.
 * For multiple types: A list of **unread objects**, to make it possible to
   list all of them in the list.

Usage
=====

There are only two ways to use subscriptions, via staticmethods of
:class:`~inyoka.core.subscriptions.models.Subscription` and by creating new
subscription types.

Managing Subscriptions
----------------------
.. currentmodule:: inyoka.core.subscriptions.models
.. automethod:: Subscription.subscribe
.. automethod:: Subscription.unsubscribe
.. automethod:: Subscription.new
.. automethod:: Subscription.accessed

.. _defining-subscription-types:

Defining Subscription Types
---------------------------
.. currentmodule:: inyoka.core.subscriptions
.. autoclass:: SubscriptionType(Component)

