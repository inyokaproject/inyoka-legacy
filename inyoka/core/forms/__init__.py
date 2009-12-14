# -*- coding: utf-8 -*-
"""
    inyoka.core.forms
    ~~~~~~~~~~~~~~~~~

    This module uses `bureaucracy <http://dev.pocoo.org/hg/bureaucracy-main/>`_
    as it's base and stays here for API reasons.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import redirect
from bureaucracy.forms import *
from bureaucracy import csrf, exceptions, recaptcha, redirects, utils, \
    widgets

from inyoka.i18n import get_translations
from inyoka.core.http import redirect_to
from inyoka.core.context import local


class Form(FormBase):
    """A somewhat extended base form to include our
    i18n mechanisms as well as other things like sessions and such stuff.
    """

    def _get_translations(self):
        """Return our translations"""
        return get_translations()

    def _lookup_request_info(self):
        """Return our current request object"""
        if hasattr(local, 'request'):
            return local.request

    def _get_wsgi_environ(self):
        """Return the WSGI environment from the request info if possible."""
        request = self._lookup_request_info()
        return request.environ if request is not None else None

    def _get_request_url(self):
        """The absolute url of the current request"""
        request = self._lookup_request_info()
        return request.build_absolute_url() if request is not None else ''

    def _redirect_to_url(self, url):
        return redirect(url)

    def _resolve_url(self, args, kwargs):
        return redirect_to(*args, **kwargs)

    def _get_session(self):
        request = self._lookup_request_info()
        return request.session if request is not None else {}

    def _autodiscover_data(self):
        request = self._lookup_request_info()
        return request.form
