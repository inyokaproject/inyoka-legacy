# -*- coding: utf-8 -*-
"""
    inyoka.core.tasks
    ~~~~~~~~~~~~~~~~~

    Tasks of the inyoka core.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from celery.decorators import task
from inyoka.context import ctx
from inyoka.core.auth.models import User
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
