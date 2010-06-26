# -*- coding: utf-8 -*-
"""
    inyoka.core.forms.form
    ~~~~~~~~~~~~~~~~~~~~~~

    Base form class.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from wtforms import Form as BaseForm
from inyoka.utils.csrf import check_request
from inyoka.context import ctx


class Form(BaseForm):

    def _get_remote_addr(self):
        req = ctx.current_request
        if req is not None:
            return req.environ['REMOTE_ADDR']

    def validate(self, extra_validators=None):
        # raises BadRequest() if csrf does not match properly
        check_request()
        return super(Form, self).validate()
