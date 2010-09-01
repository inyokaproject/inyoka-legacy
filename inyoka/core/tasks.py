# -*- coding: utf-8 -*-
"""
    inyoka.core.tasks
    ~~~~~~~~~~~~~~~~~

    Tasks of the inyoka core.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import sys
from celery.decorators import task
from collections import defaultdict
from sqlalchemy.orm.exc import NoResultFound
from inyoka.context import ctx
from inyoka.core.auth.models import User
from inyoka.core.subscriptions import SubscriptionAction
from inyoka.core.subscriptions.models import Subscription
from inyoka.core.templating import render_template
from inyoka.utils.mail import send_mail
from inyoka.core.api import _


@task
def send_activation_mail(user_id, activation_url):
    user = User.query.get(user_id)
    website_title = ctx.cfg['website_title']
    send_mail(_(u'Registration at %s') % website_title, render_template('mails/registration', {
        'user':             user,
        'activation_url':   activation_url,
        'website_title':    website_title,
    }), ctx.cfg['mail_address'], user.email)

@task
def send_notifications(object, action_name, subscriptions):
    action = SubscriptionAction.by_name(action_name)
    if action is None:
        raise ValueError('no action found with %r' % action_name)
    notifications = defaultdict(lambda: defaultdict(list))

    for s in subscriptions:
        try:
            s = Subscription.query.get(s)
        except NoResultFound, e:
            raise ValueError('no subscription found with id %r' % s)
        notifications[s.user][s.type.name].append(s.subject)

    for user in notifications:
        action.notify(user, object, notifications[user])
