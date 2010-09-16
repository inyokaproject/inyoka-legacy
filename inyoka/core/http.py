# -*- coding: utf-8 -*-
"""
    inyoka.core.http
    ~~~~~~~~~~~~~~~~

    This module implements various http helpers
    such as our own request and response classes.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from uuid import uuid4
from functools import update_wrapper
from collections import namedtuple
from werkzeug import Request as BaseRequest, Response as BaseResponse, \
    redirect, cached_property
from werkzeug.contrib.securecookie import SecureCookie
from markupsafe import escape
from inyoka.context import ctx
from inyoka.core.routing import href


class FlashMessage(namedtuple('FlashMessage', 'text success id html')):
    __slots__ = ()

    def __unicode__(self):
        if not self.html:
            return escape(self.text)
        return self.text


class Session(SecureCookie):
    """Expands the session with support for switching between permanent
    and non-permanent sessions.
    """

    def _get_permanent(self):
        return self.get('_permanent', False)

    def _set_permanent(self, value):
        self['_permanent'] = bool(value)
    permanent = property(_get_permanent, _set_permanent)


class Request(BaseRequest):
    """Our Request object with some special attributes and methods.

    :param environ: The WSGI environ.

    """

    #: the internal URL rule that matched the request.  This can be
    #: useful to inspect which methods are allowed for the URL from
    #: a before/after handler (``request.url_rule.methods``) etc.
    #:
    url_rule = None

    #: a dict of view arguments that matched the request.  If an exception
    #: happened when matching, this will be `None`.
    view_args = None

    #: if matching the URL failed, this is the exception that will be
    #: raised / was raised as part of the request handling.  This is
    #: usually a :exc:`~werkzeug.exceptions.NotFound` exception or
    #: something similar.
    routing_exception = None

    def __init__(self, *args, **kwargs):
        BaseRequest.__init__(self, *args, **kwargs)
        #: Logged database queries
        self.queries = []

    @cached_property
    def session(self):
        # hmac does not to support unicode values so we need to ensure
        # that we have a bytecode string here
        secret = ctx.cfg['secret_key'].encode('utf-8')
        name = ctx.cfg['cookie_name']
        return Session.load_cookie(self, name, secret_key=secret)

    @property
    def endpoint(self):
        """The endpoint that matched the request.  This in combination with
        :attr:`view_args` can be used to reconstruct the same or a
        modified URL.  If an exception happened when matching, this will
        be `None`.
        """
        if self.url_rule is not None:
            return self.url_rule.endpoint

    @property
    def flash_messages(self):
        buffer = self.session.get('flash_buffer', [])
        self.clear_flash_buffer()
        return buffer

    def flash(self, message, success=None, id=None, html=False):
        """Flash a message to the user."""
        if 'flash_buffer' not in self.session:
            self.session['flash_buffer'] = []
        if id is None:
            id = unicode(uuid4().get_hex())
        self.session['flash_buffer'].append(FlashMessage(message, success, id, html))
        self.session.modified = True
        return id

    def unflash(self, id):
        """Remove all messages with a given id from the flash buffer"""
        messages = [msg for msg in self.session.get('flash_buffer', ())
                    if msg.id != id]
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


def allow_next_redirects(default='portal/index'):
    """Use this decorator to ease the usage of the "next" url parameter
    for redirecting after doing some important things."""

    def decorated(func):
        def _inner(*args, **kwargs):
            req = ctx.current_request
            target = req.args.get('_next') or href(default)
            result = func(*args, **kwargs)
            if not isinstance(result, BaseResponse):
                return redirect(target)
            return result
        return update_wrapper(_inner, func)
    return decorated
