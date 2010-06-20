# -*- coding: utf-8 -*-
"""
    inyoka.utils.csrf
    ~~~~~~~~~~~~~~~~~

    Our CSRF Utilities, see http://en.wikipedia.org/wiki/Csrf for details.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPl, see LICENSE for more details.
"""
from uuid import uuid4
from inyoka.core.context import ctx
from inyoka.core.exceptions import BadRequest


def check_request(request=None):
    """
    Verfifies that request has a valid CSRF token.
    """
    request = request or ctx.current_request
    if request.method == 'POST' and ctx.cfg['enable_csrf_checks']:
        if request.is_xhr:
            # we do not check if the request is issued by one of our
            # javascript libs.  This saves some performance and don't
            # requires them to send the whole form including the csrf_token.
            # The browser checks anyway for cross-domain-issues in javascript
            # networking.
            return True
        csrf_token = request.session.pop('csrf_token', None)
        if not csrf_token or csrf_token != request.form.get('csrf_token'):
            raise BadRequest()
    return True


def generate_csrf_token():
    """
    Generate the CSRF token.
    """
    return unicode(uuid4())


def get_csrf_token(request=None):
    """
    Append the CSRF token to the current session. This is only done
    if Inyoka is configured to do so.
    """
    req = request or ctx.current_request
    if not ctx.cfg['enable_csrf_checks']:
        return u''
    session = req.session
    if 'csrf_token' not in session:
        session['csrf_token'] = generate_csrf_token()
    return session['csrf_token']
