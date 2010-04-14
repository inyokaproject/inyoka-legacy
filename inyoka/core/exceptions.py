# -*- coding: utf-8 -*-
"""
    inyoka.core.exceptions
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
# to support quite all exceptions werkzeug can raise
from werkzeug.exceptions import abort
# commonly used exceptions, more valuable using names then integers
from werkzeug.exceptions import HTTPException, Forbidden, NotFound, \
    BadRequest, Unauthorized, InternalServerError, MethodNotAllowed

__all__ = ('abort', 'HTTPException', 'Forbidden', 'NotFound',
           'BadRequest', 'Unauthorized')
