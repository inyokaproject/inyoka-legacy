# -*- coding: utf-8 -*-
"""
    inyoka.core.exceptions
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
# to support quite all exceptions werkzeug can raise
from werkzeug.exceptions import abort
# commonly used exceptions, more valuable using names then integers
from werkzeug.exceptions import HTTPException, Forbidden, NotFound, \
    BadRequest, Unauthorized, InternalServerError, MethodNotAllowed

__all__ = ('abort', 'HTTPException', 'Forbidden', 'NotFound',
           'BadRequest', 'Unauthorized', 'ImproperlyConfigured',
           'InternalServerError', 'MethodNotAllowed')


class ImproperlyConfigured(RuntimeError):
    """Some configuration error happend.

    Use this exception only if it's a value explicitly required
    as it will break the mainloop.
    """
