# -*- coding: utf-8 -*-
"""
    inyoka.utils.mail
    ~~~~~~~~~~~~~~~~~

    This module provides various e-mail related functionality.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see AUTHORS for more details.
"""
from email.mime.text import MIMEText
from email.header import Header
from subprocess import Popen, PIPE
from dns.resolver import query as dns_query
from dns.exception import DNSException
from inyoka.core.forms.validators import _mail_re


def send_mail(subject, message_, from_, to):
    """
    Send an email.
    Don't use this function directly inside controllers, but create a task for
    it.
    """
    message = u'From: %s\nTo: %s' % (from_ , to)
    message += '\nSubject: ' + Header(subject, 'utf-8', header_name='Subject').encode() + '\n'
    message += MIMEText(message_.encode('utf-8'), _charset='utf-8').as_string()
    proc = Popen(['/usr/sbin/sendmail', '-t'], stdin=PIPE)
    proc.stdin.write(message)
    proc.stdin.close()
    proc.wait()


def may_be_valid_mail(email):
    """
    Check if the mail may be valid.  This does not check the hostname part
    of the email, for that you still have to test with `may_accept_mails`.
    """
    return _mail_re.match(email) is not None


def may_accept_mails(email_or_host, timeout=2):
    """
    This function performs a DNS query on the host in the mail or the host
    provided to see if the server may accept mails.  We don't try to contact
    the SMTP server listening because most likely a server admin may flag
    this as suspicious behavior and blacklist us.
    """
    host = email_or_host.rsplit('@', 1)[-1]
    try:
        answer = list(dns_query(host, 'MX'))
        if not answer:
            raise DNSException()
    except DNSException:
        return False
    return bool(answer)
