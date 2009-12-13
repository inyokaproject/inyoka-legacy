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
from inyoka.core.api import _missing


class SubscriptionType(Component):
    """
    Must be subclassed to represent a type of Subscription.

    Values that must be defined by subclasses:
     * name: This is used to identify the type in the database and in the code,
             so it must *never ever* change.
     * object_type: A `Model` class, specifying the type of the objects
                    represented by the SubscriptionType.
     * subject_type: A `Model` class, specifying the type of the subjects
                     represented by the SubscriptionType.
     * mode: Defines the character of this SubscriptionType:
              * `multiple`: The objects don't strongly relate to each other.
                            The user is notified for each new object; in the
                            subscriptions list a link is shown for each unread
                            object.
                            Examples: topics in forum, entries in news portal.
              * `sequent`: The objects are presented in a consecutive manner,
                           The user can simply read on with the next object
                           after reading one.
                           The user is notified only once for each subject,
                           until he has accessed it; in the subscriptions list
                           only a link to the first unread object is shown.
                           Examples: posts in topic, comments in news entry.
     * is_singleton: There are no subjects, the user can just subscribe to
                     this type in general.
                     Examples: reported topics, planet suggestions.

    Methods that must be definded by subclasses:
     * get_subject(cls, object):
        A classmethod returning the subject holding the given object.
        Needs not to be defined if the class is a singleton (in the non-pythonic
        meaning; this means there are no subjects; ``is_singleton`` must be
        True in this case).
     * notify(cls, subscription, object, subject=None):
        A classmethod sending out notifications to the given user.
        It is called by :meth:`Subscription.new`.

    """
    is_singleton = False

    @classmethod
    def get_subject(cls, object):
        """
        Returns the subject holding the given object.

        Subclasses must implement this unless they are a singleton
        """
        if cls.is_singleton:
            raise ValueError('%s is a singleton, there are no subjects.' % cls.__name__)
        raise NotImplementedError

    @classmethod
    def _by_attr(cls, attrname, value=_missing):
        if value is _missing:
            map = {}
            for c in cls.get_component_classes():
                map.setdefault(getattr(c, attrname, None), []).append(c)
            return map

        return [c for c in cls.get_component_classes()
                if getattr(c, attrname, None) is value]

    @classmethod
    def by_name(cls, name=_missing):
        if name is not _missing:
            for c in cls.get_component_classes():
                if c.name == name:
                    return c
        return dict((c.name, c) for c in cls.get_component_classes())

    @classmethod
    def by_object_type(cls, object_type=_missing):
        return cls._by_attr('object_type', object_type)

    @classmethod
    def by_subject_type(cls, subject_type=_missing):
        return cls._by_attr('subject_type', subject_type)
