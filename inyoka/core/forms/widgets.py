# -*- coding: utf-8 -*-
"""
    inyoka.core.forms.widgets
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Various widgets on base of bureaucracy

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from bureaucracy.widgets import *

from inyoka.core.models import Tag
from inyoka.core.routing import href
from inyoka.core.serializer import get_serializer, primitive


class TokenInput(TextInput):
    def render(self, **attrs):
        input_html = super(TextInput, self).render(**attrs)
        tags = self._form.data[self.name]
        serializer, mime = get_serializer('json')
        ro = primitive(tags, config={
            'show_type': False,
            Tag.object_type: ('id', 'name')
        })
        tags_json = serializer(ro)
        js = """<script type="text/javascript">
$(document).ready(function () {
  $("#%s").tokenInput("%s", {'prePopulate': %s});
});
</script>""" % (self.id, href('api/core/get_tags', format='json'), tags_json)
        return input_html + js


class FixedCheckbox(Checkbox):

    def with_help_text(self, **attrs):
        """Render the checkbox with help text."""
        html = self._field.form.html_builder
        data = self(**attrs)
        if self.help_text:
            data += u' ' + html.label(self.help_text, class_='explanation',
                                      for_=self.id)
        return data

    def as_dd(self, **attrs):
        """Return a dt/dd item."""
        html = self._field.form.html_builder
        rv = []
        rv.append(html.dd(self.with_help_text()))
        label = self.label
        if label:
            rv.append(html.dt(label()))
        return u''.join(rv)

    def as_li(self, **attrs):
        """Return a li item."""
        html = self._field.form.html_builder
        rv = []
        if self.label:
            rv.append(u' ' + self.label())
        if self.help_text:
            rv.append(html.div(self.help_text, class_='explanation'))
        rv.append(self.render(**attrs))
        rv.append(self.default_display_errors())
        return html.li(u''.join(rv))

    def render(self, **attrs):
        html = self._field.form.html_builder
        self._attr_setdefault(attrs)
        return html.input(name=self.name, type='checkbox',
                          checked=self.checked, **attrs)
