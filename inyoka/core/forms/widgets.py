# -*- coding: utf-8 -*-
"""
    inyoka.core.forms.widgets
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Form library based on WTForms.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from wtforms.widgets import CheckboxInput, FileInput, HiddenInput, ListWidget, \
    PasswordInput, RadioInput, Select, SubmitInput, TableWidget, TextArea, \
    TextInput, HTMLString, Input
from inyoka.context import ctx
from inyoka.core.serializer import get_serializer, primitive
from inyoka.core.models import Tag
from inyoka.core.routing import href


SCRIPT = '''<script type="text/javascript">
$(document).ready(function() {
  %s
});
</script>
'''
TOKEN_INPUT = SCRIPT % '$("#%s").tokenInput("%s", {prePopulate: %s});'
AUTOCOMPLETE = SCRIPT % '$("#%s").autocomplete({source: "%s"});'
DATE = SCRIPT % '$("#%s").datepicker({dateFormat: "yy-mm-dd"});'


class RecaptchaWidget(object):

    def __call__(self, field, error=None, **kwargs):
        from inyoka.utils.captcha import get_recaptcha_html
        public_key = ctx.cfg['recaptcha.public_key']
        use_ssl = ctx.cfg['recaptcha.use_ssl']
        return get_recaptcha_html(public_key, use_ssl)


class TokenInput(TextInput):

    def __call__(self, field, **kwargs):
        input_html = super(TokenInput, self).__call__(field, **kwargs)
        tags = field.data or []
        serializer, mime = get_serializer('json')
        ro = primitive(tags, config={
            'show_type': False,
            Tag.object_type: ('id', 'name')
        })
        tags_json = serializer(ro)
        js = TOKEN_INPUT % (field.id, href('api/core/get_tags', format='json'),
                            tags_json)
        return HTMLString(input_html + js)


class AutocompleteWidget(TextInput):

    def __init__(self, url):
        self.url = url

    def __call__(self, field, **kwargs):
        input_html = super(TextInput, self).__call__(field, **kwargs)
        js = AUTOCOMPLETE % (field.id, href(self.url, format='json'))
        return HTMLString(input_html + js)


class DateWidget(TextInput):

    def __call__(self, field, **kwargs):
        input_html = super(TextInput, self).__call__(field, **kwargs)
        return HTMLString(input_html) + DATE % field.id


class FileInput(Input):
    """A file input field."""
    type = 'file'


class RangeWidget(object):
    def __init__(self, html):
        self.html = html

    def __call__(self, field, **kwargs):
        return HTMLString(self.html % (field[0](), field[1]()))
