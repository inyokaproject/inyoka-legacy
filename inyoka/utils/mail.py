# -*- coding: utf-8 -*-
"""
    inyoka.utils.mail
    ~~~~~~~~~~~~~~~~~

    This module provides various e-mail related functionality.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from email.mime.text import MIMEText
from email.header import Header
from subprocess import Popen, PIPE
from inyoka.core.forms.validators import _mail_re


def send_mail(subject, text, sender, recipient):
    """
    Send an email.
    Don't use this function directly inside controllers, but create a task for
    it.
    """
    message = u'From: %s\nTo: %s' % (sender, recipient)
    message += '\nSubject: ' + Header(subject, 'utf-8', header_name='Subject').encode() + '\n'
    message += MIMEText(text.encode('utf-8'), _charset='utf-8').as_string()
    proc = Popen(['/usr/sbin/sendmail', '-t'], stdin=PIPE)
    proc.stdin.write(message)
    proc.stdin.close()
    proc.wait()


def may_be_valid_mail(email):
    """
    Check if the mail may be valid.  This does not check the hostname part
    of the email.
    """
    return _mail_re.match(email) is not None
