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
from inyoka import Interface, InterfaceMeta
from inyoka.core.api import ctx
from inyoka.utils.datastructures import _missing


def subscribed(type, user, subject_id=None):
    from inyoka.core.subscriptions.models import Subscription
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
    mode
        Defines the character of this SubscriptionType:
            * **multiple**: The objects don't strongly relate to each other.
              The user is notified for each new object; in the subscriptions
              list a link is shown for each unread object.  Examples: topics
              in forum, entries in news portal.
            * **sequent**: The objects are presented in a consecutive manner,
              the user can simply read on with the next object after reading
              one. The user is notified only once for each subject, until he
              has accessed it; in the subscriptions list only a link to the
              first unread object is shown.  Examples: posts in topic,
              comments in news entry.

    **Methods that must be definded by subclasses:**

    get_subject(cls, object)
        A classmethod returning the subject holding the given object.
        Needs not to be defined if the class has no subjects (see note for
        for ``subject_type`` above)
    notify(cls, subscription, object, subject)
        A classmethod sending out notifications to the given user.
        It is called by :meth:`Subscription.new`.

    """
    is_singleton = False

    @classmethod
    def get_subject(cls, object):
        """
        Returns the subject holding the given object.

        Subclasses must implement this unless they have no subjects.
        """
        if cls.subject_type is None:
            return None
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
        return [c for c in ctx.get_implementations(cls) if action in c.actions]
