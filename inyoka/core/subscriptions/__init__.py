# -*- coding: utf-8 -*-
"""
    inyoka.core.subscriptions
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Utilities to manage subscriptions.

    Some words on terminology:
     * A subject is something that a user can subscribe to, for example a forum
       topic or a news entry.
     * The object is one element in the subject, for example a forum post or a
       comment on a news entry respectively. Each object has one subject (for
       the given examples: The topic / news entry it was posted in)

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka import Interface
from inyoka.core.api import ctx


def subscribed(type, user, subject_id=None):
    from inyoka.core.subscriptions.models import Subscription
    if isinstance(type, SubscriptionType):
        type = type.name
    return bool(Subscription.query.filter_by(user=user, type_name=type,
                                             subject_id=subject_id).count())


class SubscriptionType(Interface):
    """
    Must be subclassed to represent a type of Subscription.
    See the main docs for a more verbose description of the terms.

    **Values that must be defined by subclasses:**

    name
        This is used to identify the type in the database and in the code, so
        it must *never ever* change.
    object_type
        A :class:`~inyoka.core.database.Model` class, specifying the type of
        the objects represented by the SubscriptionType.
    subject_type
        A :class:`~inyoka.core.database.Model` class, specifying the type of
        the subjects represented by the SubscriptionType.

        It may be ``None`` for types where there are no subjects but one can
        only subscribe to the type in general, for example the whole blog or
        reported topics.
    actions
        A list of actions on whom subscriptions of the SubscriptionType
        shall be updated, i.e. which actions they shall “listen” to.

        You have to use the actions' names here, not the classes.
    mode
        Defines the character of this SubscriptionType, ``multiple`` or
        ``sequent``. See :ref:`above <subscription-modes-verbose>` for
        details.

    **Classmethods that must be definded by subclasses:**

    get_subjects(cls, object)
        A classmethod returning an iterable of subjects holding the given
        object.  Needs not to be defined if the class has no subjects (see note
        for ``subject_type`` above).

        Types where there is only one subject per object may also just define a
        `get_subject` method for convenience.  In most cases, an attrgetter
        will be sufficient.
    """
    is_singleton = False

    @classmethod
    def get_subjects(cls, object):
        """
        Returns the subjects holding the given object.

        Subclasses must implement this unless they have no subjects.
        """
        if cls.subject_type is None:
            return [None]
        if hasattr(cls, 'get_subject'):
            return [cls.get_subject(object)]
        raise NotImplementedError()

    @classmethod
    def by_name(cls, name):
        """
        Return the subscription type with the given name.
        """
        for c in ctx.get_implementations(cls):
            if c.name == name:
                return c

    @classmethod
    def by_object_type(cls, object_type):
        """
        Return all subscription types with the object type matching the given
        ``object_type``.
        """
        return [c for c in ctx.get_implementations(cls)
                if c.object_type is object_type]

    @classmethod
    def by_subject_type(cls, subject_type):
        """
        Return all subscription types with the subject type matching the given
        ``subject_type``.
        """
        return [c for c in ctx.get_implementations(cls)
                if c.subject_type is subject_type]

    @classmethod
    def by_action(cls, action=None):
        """
        Return all subscription types which implement the given action.
        """
        if not isinstance(action, basestring):
            action = action.name
        return [c for c in ctx.get_implementations(cls) if action in c.actions]


class SubscriptionAction(Interface):
    """
    Must be subclassed to represent a Subscription event.
    See the main docs for a more verbose description of the terms.

    **Values that must be defined by subclasses:**

    name
        This is used to identify the type in the database and in the code, so
        it must *never ever* change.

    **Classmethods that must be definded by subclasses:**

    notify(cls, user, object, subjects)
        A classmethod sending out notifications to the given user.
        It is called by :meth:`Subscription.new` once for every user
        and passes the new object and the matching subjects (this means: all
        subjects the user is subscribed to, not all the object has), grouped
        by type name, e.g::

            NewQuestionSubscriptionAction.notify(user23, entry1,
                {'blog.entry.by_tag': [tag1, tag2],
                 'blog.entry.by_author': [user42]})

        It must then create a suitable text and subject for the notification
        mail, honoring the different matching types.
    """

    @classmethod
    def by_name(cls, name):
        """
        Return the subscription type with the given name.
        """
        for c in ctx.get_implementations(cls):
            if c.name == name:
                return c
        raise Exception('Found no action with name %r. actions: %r' % (name, [x.name for x in ctx.get_implementations(cls)]))

    @classmethod
    def notify(cls, user, object, subjects):
        if cls == SubscriptionAction:
            raise NotImplementedError('use a subclass!')
        raise NotImplementedError('%s should have implemented this!' % cls.__name__)
