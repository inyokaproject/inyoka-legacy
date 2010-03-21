# -*- coding: utf-8 -*-
"""
    inyoka.core.forms.widgets
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Various widgets on base of bureaucracy

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from bureaucracy.widgets import *

from inyoka.core.routing import href
from inyoka.core.serializer import get_serializer, primitive


class TokenInput(TextInput):
    def render(self, **attrs):
        input_html = super(TextInput, self).render(**attrs)
        tags = self._form.data[self.name]
        serializer, mime = get_serializer('json')
        # TODO remove the reference to core.tag here
        ro = primitive(tags, config={'show_type':False, 'core.tag':('id', 'name')})
        tags_json = serializer(ro)
        js = """<script type="text/javascript">
$(document).ready(function () {
  $("#%s").tokenInput("%s", {'prePopulate':%s});
});
</script>""" % (self.id, href('api/core/get_tags', format='json'), tags_json)
        return input_html + js
