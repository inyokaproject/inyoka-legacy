# -*- coding: utf-8 -*-
"""
    inyoka.core.subscriptions.models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Models for the subscription facility.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from sqlalchemy.ext.associationproxy import association_proxy
from inyoka.core.auth.models import User
from inyoka.core.database import db
from inyoka.core.subscriptions import SubscriptionType, SubscriptionAction


def _create_subscriptionunreadobjects_by_object_id(id):
    return SubscriptionUnreadObjects(object_id=id)


class Subscription(db.Model):
    __tablename__ = 'core_subscription'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey(User.id), nullable=False)
    type_name = db.Column('type', db.Unicode(20), nullable=False)
    count = db.Column(db.Integer, nullable=False, default=0)
    subject_id = db.Column(db.Integer)
    first_unread_object_id = db.Column(db.Integer)

    user = db.relationship(User)

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
                       be considered and the action's :meth:`notify` method is
                       called.
        """
        #XXX: if `object` is removed before the task is run, subscriptions are
        #     marked as notified though the user didn't receive a notification

        if isinstance(action, basestring):
            action = SubscriptionAction.by_name(action)

        #: store ids of Subscription objects for which we need to notify
        subscriptions = []

        for t in SubscriptionType.by_action(action):
            subjects = t.get_subjects(object)
            if not subjects:
                continue
            subject_ids = [getattr(s, 'id', s) for s in subjects]

            base_cond = (Subscription.type_name == t.name)
            if t.subject_type is not None:
                base_cond &= Subscription.subject_id.in_(subject_ids)

            if t.mode == 'sequent':
                #: increment unread count where there already are unread objects
                cond = base_cond & (Subscription.count > 0)
                q = db.update(Subscription.__table__, cond,
                              {'count': Subscription.count + 1})
                db.session.execute(q)
                db.session.commit()

                #: then set the first unread object and notify the user
                #: where there were no new objects since the last visit
                cond = base_cond & (Subscription.count == 0)
                for s in Subscription.query.filter(cond):
                    subscriptions.append(s.id)
                    s.first_unread_object_id = object.id
                    s.count = 1
                db.session.commit()

            if t.mode == 'multiple':
                for s in Subscription.query.filter(base_cond):
                    subscriptions.append(s.id)
                    s.unread_object_ids.add(object.id)
                    s.count = len(s.unread_object_ids)
                db.session.commit()

        from celery.execute import send_task
        send_task('inyoka.core.tasks.send_notifications',
                  [object, action.name, subscriptions])

    @staticmethod
    def accessed(user, **kwargs):
        """
        Mark subscriptions as read.
        This means to remove objects from the `unread_objects` or unset
        `first_unread_object` (depending on the type's mode) and decrement the
        unread count.

        Must be called whenever an object is accessed.

        :param object: Mark all subscriptions with this object as read.
        :param subject: Mark all subscriptions with this subject as read.
        """
        # enforce usage of keywords
        object = kwargs.pop('object', None)
        subject = kwargs.pop('subject', None)
        assert not kwargs, 'Invalid Arguments %r' % kwargs.keys()

        if object is not None:
            for t in SubscriptionType.by_object_type(type(object)):
                subjects = t.get_subjects(object)
                if not subjects:
                    continue
                subject_ids = [getattr(s, 'id', s) for s in subjects]

                cond = ((Subscription.type_name == t.name) &
                        (Subscription.user == user))
                if t.subject_type is not None:
                    cond &= Subscription.subject_id.in_(subject_ids)
                subscriptions = Subscription.query.filter(cond).all()
                for s in subscriptions:
                    if t.mode == 'sequent':
                        s.first_unread_object_id = None
                        s.count = 0
                    elif t.mode == 'multiple':
                        try:
                            s.unread_object_ids.remove(object.id)
                        except KeyError:
                            pass
                        else:
                            s.count -= 1
                db.session.commit()

        if subject is not None:
            for t in SubscriptionType.by_subject_type(type(subject)):
                try:
                    s = Subscription.query.filter_by(type_name=t.name,
                        subject_id=subject.id, user=user).one()
                except db.NoResultFound:
                    continue

                s.count = 0
                if t.mode == 'sequent':
                    s.first_unread_object_id = None
                elif t.mode == 'multiple':
                    s.unread_object_ids = []
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

        subject_type = type_ and type_.subject_type or type(None)
        if not isinstance(subject, subject_type):
            raise ValueError('subject (%r) does not match the subject_type '
                             '(%r) of given SubscriptionType'
                             % (subject, subject_type))

        subject_id = None if subject is None else subject.id
        args = {
            'user': user,
            'type_name': type_.name,
            'subject_id': subject_id,
        }

        if Subscription.query.filter_by(**args).count():
            return False

        Subscription(**args)
        db.session.commit()
        return True

    @staticmethod
    def unsubscribe(user_or_subscription, type_=None, subject=None):
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
            assert type_ is None and subject is None
            db.session.delete(user_or_subscription)
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

        db.session.delete(s[0])
        db.session.commit()
        return True

    @property
    def type(self):
        return SubscriptionType.by_name(self.type_name)

    @property
    def subject(self):
        if None not in (self.type.subject_type, self.subject_id):
            return self.type.subject_type.query.get(self.subject_id)


class SubscriptionUnreadObjects(db.Model):
    __tablename__ = 'core_subscription_unread_objects'
    __table_args__ = (
        db.UniqueConstraint('subscription_id', 'object_id'),
        {}
    )

    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.ForeignKey(Subscription.id), nullable=False)
    object_id = db.Column(db.Integer, nullable=False)

    subscription = db.relationship(Subscription,
        backref=db.backref('_unread_object_ids', order_by=id,
                collection_class=set, cascade='all, delete, delete-orphan'))

    def __repr__(self):
        return '<SubscriptionUnreadObjects s %r obj %r>' % \
                (self.subscription_id, self.object_id)
