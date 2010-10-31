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
from inyoka.i18n import get_translations
from inyoka.core.api import _
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
    req = request or ctx.current_request or None
    if not req:
        return u''

    session = req.session
    if 'csrf_token' not in session or force_reset:
        session['csrf_token'] = generate_csrf_token()
    return session['csrf_token']


class Form(BaseForm):
    """This form implements basic CSRF protection."""

    csrf = fields.HiddenField(u' ')

    #: Set this to `True` to disable all csrf checks on this form.
    #: Note: This overrides global csrf settings!
    csrf_disabled = False

    def __init__(self, formdata=None, *args, **kwargs):
        csrf_token = get_csrf_token()
        super(Form, self).__init__(formdata, csrf=csrf_token, *args, **kwargs)

    def _get_translations(self):
        """Hook our translations into wtforms"""
        return get_translations()

    def validate_csrf(self, field):
        enabled = (ctx.cfg['enable_csrf_checks'] and
                   not self.csrf_disabled and
                   ctx.current_request)
        if not enabled or ctx.current_request.is_xhr:
            return

        csrf_token = get_csrf_token()
        is_valid = field.data and unicode(field.data) == csrf_token

        # reset this field, otherwise stale token is displayed
        field.data = get_csrf_token()

        if not is_valid:
            raise BadRequest('Invalid CSRF token.')

    def validate_on_submit(self):
        return ctx.current_request.method in ("POST", "PUT") and self.validate()


class MagicFilterForm(Form):
    """
    A Form you can use as an elegant filtering UI.
    Of the form fields specified in `dynamic_fields` only those are displayed
    that were filled out the last time the form was submitted.
    Fields that are not in  `dynamic_fields` remain uninfluenced.
    If you want to show all fields, set `expand_all` on initialization (usually
    you want this behaviour when presenting the form the first time to the user,
    before he filled anything out).
    Use this form in combination with `magic_filter_form` of the template
    utilities.
    """
    dynamic_fields = None

    def __init__(self, formdata=None, expand_all=False, *args, **kwargs):
        self.expand_all = expand_all

        if not expand_all:
            choices = [(x,x) for x in self.dynamic_fields]
            self._unbound_fields += [
                ('new_field', fields.SelectField(choices=choices)),
                ('add_field', fields.SubmitField(_(u'Add filter')))]

        Form.__init__(self, formdata=formdata, *args, **kwargs)

    def validate(self, *args, **kwargs):
        rv = Form.validate(self, *args, **kwargs)
        self.new_field.choices = []
        data = self.data.get

        # regenerate `new_field` choices to show only fields that are not added
        # and remove fields from the form that are neither filled out nor added.
        for field_name in self.dynamic_fields:
            # `field_name` was added if `new_field` is set to it's name and if
            # the `add_field` button was pressed
            was_added = (field_name == data('new_field')) and data('add_field')
            if not (data(field_name) or was_added):
                self.new_field.choices += [(field_name, self._fields[field_name].label.text)]
                self._fields.pop(field_name)
        
        return rv
