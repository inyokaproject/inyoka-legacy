# -*- coding: utf-8 -*-
"""
    inyoka.core.subscriptions.models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Models for the subscription facility.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from sqlalchemy.ext.associationproxy import association_proxy
from inyoka.core.auth.models import User
from inyoka.core.database import db
from inyoka.core.subscriptions import SubscriptionType

def _create_subscriptionunreadobjects_by_object_id(id):
    return SubscriptionUnreadObjects(object_id=id)


class Subscription(db.Model):
    __tablename__ = 'core_subscription'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey(User.id), nullable=False)
    type_name = db.Column('type', db.String(20), nullable=False)
    count = db.Column(db.Integer, nullable=False, default=0)
    subject_id = db.Column(db.Integer)
    first_unread_object_id = db.Column(db.Integer)

    user = db.relation(User)

    unread_object_ids = association_proxy('_unread_object_ids', 'object_id',
        creator=_create_subscriptionunreadobjects_by_object_id)

    @staticmethod
    def new(object, types=None):
        """
        Sends notifications for a new object, saves it as `first_unread_object`
        or in `unread_objects` (depending on the type's mode) and increments
        the unread count.

        Must be called whenever a new object is created or moved to the scope
        of a SubscriptionType (e.g. when a topic is moved to another forum).

        :param object: The added object.
        :param types: If given, only subscriptions of the given type(s) are
                      included.
        """
        if types is None:
            types = SubscriptionType.by_object_type(type(object))
        else:
            if not hasattr(type, '__iter__'):
                types = [types]
            types = [isinstance(t, basestring)
                     and SubscriptionType.by_name(t) or t for t in types]

        for t in types:
            if t.is_singleton:
                subject = subject_id = None
            else:
                subject = t.get_subject(object)
                subject_id = subject.id

            for s in Subscription.query.filter_by(type_name=t.name,
                                                  subject_id=subject_id):
                if t.mode == 'sequent':
                    if not s.count:
                        t.notify(s, object, subject)
                        s.first_unread_object_id = object.id
                        s.count = 1
                    else:
                        s.count += 1
                if t.mode == 'multiple':
#                s.unread_objects.add(object)
                    s.unread_object_ids.add(object.id)
                    t.notify(s, object, subject)
                    s.count += 1
            db.session.commit()

    @staticmethod
    def accessed(user, object):
        """
        Removes the object from the `unread_objects` or unsets
        `first_unread_object` (depending on the type's mode) and decrements
        the unread count.

        Must be called whenever an object is accessed.
        """
        for t in SubscriptionType.by_object_type(type(object)):
            if t.is_singleton:
                subject = subject_id = None
            else:
                subject = t.get_subject(object)
                subject_id = getattr(subject, 'id', subject)

            try:
                s = Subscription.query.filter_by(type_name=t.name,
                    subject_id=subject_id, user=user).one()
            except db.NoResultFound:
                pass
            else:
                if t.mode == 'sequent':
                    s.first_unread_object_id = None
                    s.count = 0
                elif t.mode == 'multiple':
                    s.unread_object_ids.remove(object.id)
                    s.count -= 1
                db.session.commit()

    @staticmethod
    def subscribe(user, type, subject=None):
        """
        Safely subscribe a user to a subject.
        Returns False if the Subscription already exists, else True.
        """
        if isinstance(type, basestring):
            type = SubscriptionType.by_name(type)

        if not type.is_singleton and subject is None:
            raise ValueError('No subject specified')
            #TODO: also validate this in the MapperExtension?

        args = {
            'user': user,
            'type_name': type.name,
            'subject_id': getattr(subject, 'id', subject),
        }

        if Subscription.query.filter_by(**args).count():
            return False

        db.session.add(Subscription(**args))
        db.session.commit()
        return True

    @staticmethod
    def unsubscribe(user_or_subscription, type, subject=None):
        """
        Safely unsubscribe a user from a subject.
        Returns False if the Subscription did not exist, else True.
        """
        if isinstance(user_or_subscription, Subscription):
            assert type is None and subject is None
            db.session.remove(user_or_subscription)
            db.session.commit()
            return True
        else:
            user = user_or_subscription

        if isinstance(type, basestring):
            type = SubscriptionType.by_name(type)

        s = Subscription.query.filter_by(user=user, type_name=type.name,
            subject_id=getattr(subject, 'id', subject)).all()

        if not len(s):
            return False
        if len(s) > 1:
            raise ValueError('Duplicate found!')

        db.session.remove(s[0])
        db.session.commit()
        return True





class SubscriptionUnreadObjects(db.Model):
    __tablename__ = 'core_subscription_unread_objects'
    __table_args__ = (
        db.UniqueConstraint('subscription_id', 'object_id'),
        {}
    )

    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.ForeignKey(Subscription.id), nullable=False)
    object_id = db.Column(db.Integer, nullable=False)

    subscription = db.relation(Subscription,
        backref=db.backref('_unread_object_ids', order_by=id,
                collection_class=set, cascade='all, delete, delete-orphan'))

    def __repr__(self):
        return '<SubscriptionUnreadObjects s %r obj %r>' % \
                (self.subscription_id, self.object_id)


class SubscriptionSchemaController(db.ISchemaController):
    models = [SubscriptionUnreadObjects, Subscription]
