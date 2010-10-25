# -*- coding: utf-8 -*-
"""
    inyoka.core.mixins
    ~~~~~~~~~~~~~~~~~~

    Various mixins for model extension.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.markup.parser import parse, render
from inyoka.utils.diff3 import prepare_udiff, generate_udiff


class TextRendererMixin(object):
    """Mixin that renders the text to `rendered_text` when set.  Combine
    with a synonym column mapping for `text` to `_text`.
    """

    #: The function that is called to render the text
    text_renderer = lambda s, v: render(parse(v), format='html')
    #: If the text was rendered or not
    _rendered = False

    def __init__(self, *args, **kwargs):
        super(TextRendererMixin, self).__init__(*args, **kwargs)
        self._render()

    def _get_text(self):
        return self._text

    def _set_text(self, value):
        if self._text == value:
            # don't render the text if nothing changed
            return
        self._text = value
        self._render()

    def _render(self):
        """Render the entries text and save it to `rendered_text`."""
        if self._text is not None:
            self.rendered_text = unicode(self.text_renderer(self._text))

    text = property(_get_text, _set_text)
    del _get_text, _set_text
