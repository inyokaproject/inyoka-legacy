# -*- coding: utf-8 -*-
"""
    inyoka.core.http
    ~~~~~~~~~~~~~~~~

    This module implements various http helpers
    such as our own request and response classes.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from time import time
from hashlib import md5
from operator import itemgetter
from werkzeug import Request as BaseRequest, Response as BaseResponse, \
    redirect, get_current_url, cached_property
from werkzeug.contrib.securecookie import SecureCookie
from inyoka.core.context import ctx
from inyoka.core.routing import href


class FlashMessage(tuple):
    __slots__ = ()

    def __new__(self, text, success=None, id=None):
        return tuple.__new__(self, (text, success, intern(str(id))))

    text = property(itemgetter(0))
    success = property(itemgetter(1))
    id = property(itemgetter(2))

    def __repr__(self):
        return '<%s(%s:%s)>' % (
            self.__class__.__name__,
            self.text,
            self.success
        )


class Request(BaseRequest):
    """Our Request object with some special attributes and methods.

    :param environ: The WSGI environ.

    """

    def __init__(self, *args, **kwargs):
        BaseRequest.__init__(self, *args, **kwargs)
        #: Logged database queries
        self.queries = []

    @cached_property
    def current_url(self):
        """Get the current absolute URL from the WSGI environ"""
        return get_current_url(self.environ)

    @cached_property
    def session(self):
        # hmac does not to support unicode values so we need to ensure
        # that we have a bytecode string here
        secret = ctx.cfg['secret_key'].encode('utf-8')
        name = ctx.cfg['cookie_name']
        return SecureCookie.load_cookie(self, name, secret_key=secret)

    @property
    def flash_messages(self):
        buffer = self.session.get('flash_buffer', [])
        self.clear_flash_buffer()
        return buffer

    def flash(self, message, success=None, id=None):
        """Flash a message to the user."""
        if 'flash_buffer' not in self.session:
            self.session['flash_buffer'] = []
        if id is None:
            id = md5(str(time()) + ctx.cfg['secret_key'] + message).hexdigest()
        self.session['flash_buffer'].append(FlashMessage(message, success, id))
        self.session.modified = True
        return id

    def unflash(self, id):
        """Remove all messages with a given id from the flash buffer"""
        messages = [msg for msg in self.session.get('flash_buffer', ())
                    if msg.id != str(id)]
        self.session['flash_buffer'] = messages
        self.session.modified = True

    def clear_flash_buffer(self):
        """Clear the whole flash buffer."""
        return self.session.pop('flash_buffer', None)

    def has_flashed_messages(self):
        return bool(self.session.get('flash_buffer', None))


class Response(BaseResponse):
    """Our default response class with default mimetype to text/html"""
    default_mimetype = 'text/html'

    def prevent_caching(self):
        """Prevent downstream proxies from caching this page"""
        self.headers['Cache-Control'] = 'no-cache, must-revalidate'
        self.headers['Pragma'] = 'no-cache'
        self.headers['Expires'] = '-1'


def redirect_to(endpoint, **kwargs):
    """Temporarily redirect to an URL rule."""
    return redirect(href(endpoint, **kwargs))
