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

from inyoka.i18n import get_locale, get_translations
from inyoka.core.http import redirect
from inyoka.core.context import current_request


class Form(FormBase):
    """A somewhat extended base form to include our
    i18n mechanisms as well as other things like sessions and such stuff.
    """

    def _get_translations(self):
        """Return our translations"""
        return get_translations(get_locale())

    def _lookup_request_info(self):
        """Return our current request object"""
        return current_request

    def _get_wsgi_environ(self):
        """Return the WSGI environment from the request info if possible."""
        if current_request:
            return current_request.environ

    def _get_request_url(self):
        """The absolute url of the current request"""
        if current_request:
            return current_request.build_absolute_url()
        return ''

    def _redirect_to_url(self, url):
        return redirect(url)

    def _resolve_url(self, args, kwargs):
        return redirect_to(*args, **kwargs)

    def _get_session(self):
        return current_request.session if current_request != None else {}


