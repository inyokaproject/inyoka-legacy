# -*- coding: utf-8 -*-
"""
    inyoka.core.forms.widgets
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Form library based on WTForms.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from wtforms.widgets import *
from wtforms.widgets import HTMLString, TextInput, HiddenInput, Input
from inyoka.context import ctx


TOKEN_INPUT = '''
<script type="text/javascript">
$(document).ready(function () {
  $("#%s").tokenInput("%s", {'prePopulate': %s});
});
</script>
'''


class RecaptchaWidget(object):

    def __call__(self, field, error=None, **kwargs):
        from inyoka.utils.recaptcha import get_recaptcha_html
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
        js =  TOKEN_INPUT % (field.id, href('api/core/get_tags', format='json'),
                             tags_json)
        return HTMLString(input_html + js)


class FileInput(Input):
    """A file input field."""
    type = 'file'

