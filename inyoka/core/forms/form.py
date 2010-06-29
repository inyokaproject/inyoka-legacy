# -*- coding: utf-8 -*-
"""
    inyoka.core.forms.form
    ~~~~~~~~~~~~~~~~~~~~~~

    Base form class.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from uuid import uuid4
from wtforms import Form as BaseForm
from inyoka.core.forms import fields
from inyoka.core.exceptions import BadRequest
from inyoka.context import ctx


def generate_csrf_token():
    """
    Generate the CSRF token.
    """
    return unicode(uuid4())


def get_csrf_token(request=None, force_reset=False):
    """
    Append the CSRF token to the current session. This is only done
    if Inyoka is configured to do so.  Set `force_reset` to True if you
    want to reset the current csrf token in the session.
    """
    req = request or ctx.current_request
    session = req.session
    if 'csrf_token' not in session or force_reset:
        session['csrf_token'] = generate_csrf_token()
    return session['csrf_token']


class Form(BaseForm):

    csrf = fields.HiddenField()

    #: Set this to `True` to disable all csrf checks on this form.
    #: Note: This overrides global csrf settings!
    csrf_disabled = False

    def __init__(self, formdata=None, *args, **kwargs):
        if formdata is None:
            formdata = ctx.current_request.form

        csrf_token = get_csrf_token(force_reset=False)

        super(Form, self).__init__(formdata, csrf=csrf_token, *args, **kwargs)

    def _get_remote_addr(self):
        req = ctx.current_request
        if req is not None:
            return req.environ['REMOTE_ADDR']

    def validate_csrf(self, field):
        enabled = not self.csrf_disabled or ctx.cfg['enable_csrf_checks']
        if not enabled or ctx.current_request.is_xhr:
            return

        csrf_token = get_csrf_token()
        is_valid = field.data and field.data == csrf_token

        # reset this field, otherwise stale token is displayed
        field.data = get_csrf_token(force_reset=True)

        if not is_valid:
            raise BadRequest()

    def validate_on_submit(self):
        return request.method in ("POST", "PUT") and self.validate()
