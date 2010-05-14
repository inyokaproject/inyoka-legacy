# -*- coding: utf-8 -*-
"""
    inyoka.core.auth.decorators
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Various decorators to ease the usage with the auth modules.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from functools import wraps
from inyoka.i18n import _
from inyoka.core.http import redirect_to
from inyoka.core.context import ctx


def login_required(func):
    """Require an authenticated user.

    If the user is not authenticated he is redirected to the proper
    login form.
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        if ctx.current_request.user.is_anonymous:
            ctx.current_request.flash(_(u'You must login to view this!'))
            return redirect_to('portal/login', _next=ctx.current_request.url)
        return func(*args, **kwargs)
    return decorated
