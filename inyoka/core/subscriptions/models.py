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
from inyoka.utils.datastructures import _missing

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
    def new(object, action):
        """
        Sends notifications for a new object, saves it as `first_unread_object`
        or in `unread_objects` (depending on the type's mode) and increments
        the unread count.

        Must be called whenever a new object is created or moved to the scope
        of a SubscriptionType (e.g. when a topic is moved to another forum).

        :param object: The added object.
        :param action: The action which lead to the creation of the object.
                       It is used to select the SubscriptionTypes that need to
                       be considered, it is also passed to the :meth:`notify`
                       method to allow customizing the notification text.
        """
        for t in SubscriptionType.by_action(action):
            subject = t.get_subject(object)
            subject_id = getattr(subject, 'id', None)

            if t.mode == 'sequent':
                for s in Subscription.query.filter_by(type_name=t.name,
                                                      subject_id=subject_id,
                                                      count=0):
                    t.notify(s, object, subject)
                    s.first_unread_object_id = object.id
                    s.count = 1
                db.session.commit()

                q = db.update(Subscription.__table__,
                      (Subscription.type_name == t.name) &
                      (Subscription.subject_id == subject_id) &
                      (Subscription.count > 0),
                      {'count': Subscription.count + 1}
                     )
#                print 'updated (%r %r %r):' % (t.name, object, action),\
#                    db.session.execute(db.select([Subscription.__table__],
#                      (Subscription.type_name == t.name) &
#                      (Subscription.subject_id == subject_id) &
#                      (Subscription.count > 0))).fetchall()
                db.session.execute(q)
                db.session.commit()

            if t.mode == 'multiple':
                for s in Subscription.query.filter_by(type_name=t.name,
                                                      subject_id=subject_id):
                    s.unread_object_ids.add(object.id)
                    t.notify(s, object, subject)
                    s.count = len(s.unread_object_ids)
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
    def subscribe(user, type_, subject=None):
        """
        Safely subscribe a user to a subject.
        Returns False if the Subscription already exists, else True.

        :param user: A user object or a user id.
        :param type_: The subscription type to be used. May be a subclass of
                      :class:`SubscriptionType` or a name of a subscription
                      type.
        :param subject: The subject to be used (id or instance). May be None
                        if the type has not ``subject_type``.
        """
        if isinstance(type_, basestring):
            type_ = SubscriptionType.by_name(type_)

#        if type_.subject_type is not None and subject is None:
#            raise ValueError('No subject specified')
#            #TODO: also validate this in the MapperExtension?
#
        subject_type = type_.subject_type or type(None)
        if not isinstance(subject, subject_type):
            raise ValueError('subject (%r) does not match the subject_type '
                             '(%r) of given SubscriptionType'
                             % (subject, type_.subject_type))

        subject_id = None if subject is None else subject.id
        args = {
            'user': user,
            'type_name': type_.name,
            'subject_id': subject_id,
        }

        if Subscription.query.filter_by(**args).count():
            return False

        sub = Subscription(**args)
        db.session.commit()
        return True

    @staticmethod
    def unsubscribe(user_or_subscription, type_=_missing, subject=None):
        """
        Safely unsubscribe a user from a subject.
        Returns False if the Subscription did not exist, else True.

        :param user_or_subscription: A user object or a user id.
                                     May also be a Subscription object, in
                                     this case the other parameters must not
                                     be given.
        :param type_: The subscription type to be used. May be a subclass of
                      :class:`SubscriptionType` or a name of a subscription
                      type.
        :param subject: The subject to be used (id or instance). May be None
                        if the type has not ``subject_type``.
        """
        if isinstance(user_or_subscription, Subscription):
            assert type_ is _missing and subject is None
            db.session.remove(user_or_subscription)
            db.session.commit()
            return True
        else:
            user = user_or_subscription

        if isinstance(type_, basestring):
            type_ = SubscriptionType.by_name(type_)

        s = Subscription.query.filter_by(user=user, type_name=type_.name,
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
