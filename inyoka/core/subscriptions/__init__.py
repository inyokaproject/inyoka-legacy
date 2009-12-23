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

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka import Component
from inyoka.core.api import ctx
from inyoka.utils.datastructures import _missing


class SubscriptionType(Component):
    """
    Must be subclassed to represent a type of Subscription.

    **Values that must be defined by subclasses:**

    name
        This is used to identify the type in the database and in the code, so it must *never ever* change.
    object_type
        A :class:`~inyoka.core.database.Model` class, specifying the type of
        the objects represented by the SubscriptionType.
    subject_type
        A :class:`~inyoka.core.database.Model` class, specifying the type of
        the subjects represented by the SubscriptionType.

        It may be ``None`` for types where there are no subjects but one can
        only subscribe to the type in general, for example the whole blog or
        reported topics.
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
        raise NotImplementedError

    #XXX: we should set the stuff below on setup (add an after_setup() method
    #     for components or something)

    @classmethod
    def _by_attr(cls, attrname, value=_missing):
        if value is _missing:
            map = {}
            for c in ctx.get_component_classes(cls):
                map.setdefault(getattr(c, attrname, None), []).append(c)
            return map

        return [c for c in ctx.get_component_classes(cls)
                if getattr(c, attrname, None) is value]

    @classmethod
    def by_name(cls, name=_missing):
        if name is not _missing:
            for c in ctx.get_component_classes(cls):
                if c.name == name:
                    return c
        return dict((c.name, c) for c in ctx.get_component_classes(cls))

    @classmethod
    def by_object_type(cls, object_type=_missing):
        return cls._by_attr('object_type', object_type)

    @classmethod
    def by_subject_type(cls, subject_type=_missing):
        return cls._by_attr('subject_type', subject_type)

    @classmethod
    def by_action(cls, action=None):
        if action is None:
            map = {}
            for c in ctx.get_component_classes(cls):
                for action in c.actions:
                    map.setdefault(action, []).append(c)
            return map
        return [c for c in ctx.get_component_classes(cls) if action in c.actions]
