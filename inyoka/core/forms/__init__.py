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

from inyoka.core.http import _redirect, redirect_to
