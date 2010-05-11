# -*- coding: utf-8 -*-
"""
    inyoka.utils.csrf
    ~~~~~~~~~~~~~~~~~

    Our CSRF Utilities, see http://en.wikipedia.org/wiki/Csrf for details.

    :copyright: 2010 by the Project Name Team, see AUTHORS for more details.
    :license: GNU GPl, see LICENSE for more details.
"""
import os
from time import time
from hashlib import sha256
from inyoka.core.context import ctx
from inyoka.core.exceptions import BadRequest


def check_request(request=None):
    request = request or ctx.current_request
    if request.method == 'POST' and ctx.cfg['enable_csrf_checks']:
        if request.is_xhr:
            # .is_xhr() is based on the presence of X-Requested-With.  In
            # the context of a browser, this can only be sent if using
            # XmlHttpRequest.  Browsers implement careful policies for
            # XmlHttpRequest:
            #
            #  * Normally, only same-domain requests are allowed.
            #
            #  * Some browsers (e.g. Firefox 3.5 and later) relax this
            #    carefully:
            #
            #    * if it is a 'simple' GET or POST request (which can
            #      include no custom headers), it is allowed to be cross
            #      domain.  These requests will not be recognized as AJAX.
            #
            #    * if a 'preflight' check with the server confirms that the
            #      server is expecting and allows the request, cross domain
            #      requests even with custom headers are allowed. These
            #      requests will be recognized as AJAX, but can only get
            #      through when the developer has specifically opted in to
            #      allowing the cross-domain POST request.
            #
            # So in all cases, it is safe to allow these requests through.
            return True
        csrf_token = request.session.pop('csrf_token', None)
        if not csrf_token or csrf_token != request.form.get('csrf_token'):
            raise BadRequest()
    return True


def generate_csrf_token():
    return sha256((ctx.cfg['secret_key'] + unicode(time())).encode('utf-8')).hexdigest()


def get_csrf_token(request=None):
    req = request or ctx.current_request
    if not ctx.cfg['enable_csrf_checks']:
        return u''
    session = req.session
    if 'csrf_token' not in session:
        session['csrf_token'] = generate_csrf_token()
    return session['csrf_token']
