# -*- coding: utf-8 -*-
"""
    inyoka.core.forms
    ~~~~~~~~~~~~~~~~~

    This module uses `bureaucracy <http://dev.pocoo.org/hg/bureaucracy-main/>`_
    as it's base and stays here for API reasons.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from bureaucracy.forms import *
from bureaucracy import csrf, exceptions, recaptcha, redirects, utils, \
    widgets

from inyoka.core.i18n import get_locale, get_translations
from inyoka.core.http import redirect
from inyoka.core.context import get_request


class Form(FormBase):
    """A somewhat extended base form to include our
    i18n mechanisms as well as other things like sessions and such stuff.
    """

    def _get_translations(self):
        """Return our translations"""
        return get_translations(get_locale())

    def _lookup_request_info(self):
        """Return our current request object"""
        return get_request()

    def _get_wsgi_environ(self):
        """Return the WSGI environment from the request info if possible."""
        req = get_request()
        if req is not None:
            return req.environ

    def _get_request_url(self):
        """The absolute url of the current request"""
        req = get_request()
        if req is not None:
            return req.build_absolute_url()
        return ''

    def _redirect_to_url(self, url):
        return redirect(url)

    def _resolve_url(self, args, kwargs):
        return redirect_to(*args, **kwargs)

    def _get_session(self):
        #TODO: implement this once we have a session system.
        raise NotImplementedError('some features require access to the session. '
                                  'If you want those, implement `_get_session`.')
