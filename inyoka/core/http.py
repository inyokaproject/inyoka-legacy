# -*- coding: utf-8 -*-
"""
    inyoka.core.http
    ~~~~~~~~~~~~~~~~

    This module implements various http helpers
    such as our own request and response classes.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import Request as BaseRequest, Response as BaseResponse, \
    redirect as _redirect, get_current_url, cached_property
from werkzeug.contrib.securecookie import SecureCookie
from inyoka.core.context import config
from inyoka.core.routing import href


class FlashMessage(object):

    def __init__(self, text, success=None, id=None):
        self.text = text
        self.success = success
        self.id = id

    def __repr__(self):
        return '<%s(%s:%s)>' % (
            self.__class__.__name__,
            self.text,
            self.success
        )

    def __reduce__(self):
        items = (self.text, self.success, self.id)
        dict_ = vars(self).copy()
        return (self.__class__, items, dict_)


class Request(BaseRequest):
    """Our Request object with some special attributes and methods.

    :param environ: The WSGI environ.
    :param application: The current application instance.

    """

    def __init__(self, environ, application):
        self.application = application
        BaseRequest.__init__(self, environ)

    def build_absolute_url(self):
        """Get the current absolute URL from the WSGI environ"""
        return get_current_url(self.environ)

    @cached_property
    def session(self):
        # hmac does not to support unicode values so we need to ensure
        # that we have a bytecode string here
        secret = config['cookie_secret'].encode('utf-8')
        name = config['cookie_name']
        return SecureCookie.load_cookie(self, name, secret_key=secret)

    @property
    def flash_messages(self):
        buffer = self.session.get('flash_buffer', [])
        self.clear_flash_buffer()
        return buffer

    def flash(self, message, success=None, id=None):
        """Flash a message to the user."""
        if not 'flash_buffer' in self.session:
            self.session['flash_buffer'] = []
        self.session['flash_buffer'].append(FlashMessage(message, success, id))
        self.session.modified = True
        return True

    def unflash(self, id):
        """Remove all messages with a given id from the flash buffer"""
        messages = [msg for msg in self.session.get('flash_buffer', ())
                    if msg.id != id]
        self.session['flash_buffer'] = messages

    def clear_flash_buffer(self):
        """Clear the whole flash buffer."""
        self.session.pop('flash_buffer', None)

    def has_flashed_messages(self):
        return bool(self.session.get('flash_buffer', None))


class Response(BaseResponse):
    """Our default response class with default mimetype to text/html"""
    default_mimetype = 'text/html'


class DirectResponse(Exception):
    """A :exc:`DirectResponse` is used to pass a response object
    to the user without executing any other routing or middleware
    dispatching.

    """

    def __init__(self, response):
        Exception.__init__(self, response)
        self.message = 'direct response %r' % response
        self.response = response


def redirect_to(*args, **kwargs):
    """Temporarily redirect to an URL rule."""
    return _redirect(href(*args, **kwargs))
