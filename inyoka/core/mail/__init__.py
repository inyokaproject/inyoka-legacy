#-*- coding: utf-8 -*_
"""
    inyoka.core.mail
    ~~~~~~~~~~~~~~~~

    This module implements some email-realted functions and classes.

    It is based on :mod:`zine.utils.mail` and :mod:`django.core.mail`
    but adapted to match the inyoka component framework.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import re
import urlparse
from email.mime.text import MIMEText
from smtplib import SMTP, SMTPException
from urlparse import urlparse
from inyoka.i18n import _
from inyoka.context import ctx
from inyoka.core.config import TextConfigField, BooleanConfigField, \
    IntegerConfigField
from inyoka.core.forms.validators import is_valid_email, check
from inyoka.utils.urls import get_host_port_mapping, make_full_domain
from inyoka.utils.logger import logger


#: Used to split various formats of email addresses
_mail_split_re = re.compile(r'^(.*?)(?:\s+<(.+)>)?$')

#: outbox used for unittesting
outbox = []

# Configuration values
email_log_only = BooleanConfigField('email.log_only', default=False)
email_system_email = TextConfigField('email.system_email',
    default=u'noreply@%s' % (ctx.cfg['base_domain_name'].split(':')[0]))

email_smtp_host = TextConfigField('email.smtp_host', default=u'localhost')
email_smtp_port = IntegerConfigField('email.smtp_port', default=25)
email_smtp_user = TextConfigField('email.smtp_user', default=u'')
email_smtp_password = TextConfigField('email.smtp_password', default=u'')
email_smtp_use_tls = BooleanConfigField('email.smtp_use_tls', default=False)


def split_email(s):
    """Split a mail address:

    >>> split_email("John Doe")
    ('John Doe', None)
    >>> split_email("John Doe <john@doe.com>")
    ('John Doe', 'john@doe.com')
    >>> split_email("john@doe.com")
    (None, 'john@doe.com')
    """
    p1, p2 = _mail_split_re.search(s).groups()
    if p2:
        return p1, p2
    elif check(is_valid_email, p1):
        return None, p1
    return p1, None


def send_email(subject, text, to_addrs, quiet=True):
    """Send a mail using the :class:`EMail` class."""
    e = EMail(subject, text, to_addrs)
    if ctx.cfg['email.log_only']:
        return e.log()
    if quiet:
        return e.send_quiet()
    return e.send()


class EMail(object):
    """Represents one E-Mail message that can be sent."""

    def __init__(self, subject=None, text='', to_addrs=None):
        self.subject = u' '.join(subject.splitlines())
        self.text = text
        from_addr = ctx.cfg['email.system_email']
        self.from_addr = u'%s <%s>' % (ctx.cfg['website_title'], from_addr)
        self.to_addrs = []
        if isinstance(to_addrs, basestring):
            self.add_addr(to_addrs)
        else:
            for addr in to_addrs:
                self.add_addr(addr)

    def add_addr(self, addr):
        """Add an mail address to the list of recipients"""
        lines = addr.splitlines()
        if len(lines) != 1:
            raise ValueError(_(u'invalid value for email address'))
        self.to_addrs.append(lines[0])

    def as_message(self):
        """Return the email as MIMEText object."""
        if not self.subject or not self.text or not self.to_addrs:
            raise RuntimeError(_(u'Not all mailing parameters filled in'))

        msg = MIMEText(self.text.encode('utf-8'))

        #: MIMEText sucks, it does not override the values on
        #: setitem, it appends them.  We get rid of some that
        #: are predefined under some versions of python
        del msg['Content-Transfer-Encoding']
        del msg['Content-Type']

        msg['From'] = self.from_addr.encode('utf-8')
        msg['To'] = ', '.join(x.encode('utf-8') for x in self.to_addrs)
        msg['Subject'] = self.subject.encode('utf-8')
        msg['Content-Transfer-Encoding'] = '8bit'
        msg['Content-Type'] = 'text/plain; charset=utf-8'
        return msg

    def format(self, sep='\r\n'):
        """Format the message into a string."""
        return sep.join(self.as_message().as_string().splitlines())

    def log(self):
        """Logs the email"""
        logger.debug('%s\n%s\n\n' % ('-' * 79, self.format('\n').rstrip()))
        if ctx.cfg['testing']:
            outbox.append(self.as_message().as_string())

    def send(self):
        """Send the message."""
        try:
            smtp = SMTP(ctx.cfg['email.smtp_host'], ctx.cfg['email.smtp_port'])
        except SMTPException, e:
            raise RuntimeError(str(e))

        if ctx.cfg['email.smtp_use_tls']:
            smtp.ehlo()
            if not smtp.esmtp_features.has_key('starttls'):
                raise RuntimeError(_(u'TLS enabled but server does not '
                                     u'support TLS'))
            smtp.starttls()
            smtp.ehlo()

        if ctx.cfg['email.smtp_user']:
            try:
                smtp.login(ctx.cfg['email.smtp_user'],
                           ctx.cfg['email.smtp_password'])
            except SMTPException, e:
                raise RuntimeError(str(e))

        msgtext = self.format()
        try:
            try:
                return smtp.sendmail(self.from_addr, self.to_addrs, msgtext)
            except SMTPException, e:
                raise RuntimeError(str(e))
        finally:
            if ctx.cfg['email.smtp_use_tls']:
                # avoid false failure detection when the server closes
                # the SMTP connection with TLS enabled
                import socket
                try:
                    smtp.quit()
                except socket.sslerror:
                    pass
            else:
                smtp.quit()

    def send_quiet(self):
        """Send the message, swallowing exceptions."""
        try:
            return self.send()
        except Exception:
            return
