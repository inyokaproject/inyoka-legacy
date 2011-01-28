# -*- coding: utf-8 -*-
"""
    inyoka.core.forms
    ~~~~~~~~~~~~~~~~~

    Form library based on WTForms.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.forms import validators, widgets
from inyoka.core.forms.fields import *
from inyoka.core.forms.form import Form, get_csrf_token, MagicFilterForm
from inyoka.core.forms.validators import ValidationError
