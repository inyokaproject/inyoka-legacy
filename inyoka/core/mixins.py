# -*- coding: utf-8 -*-
"""
    inyoka.core.mixins
    ~~~~~~~~~~~~~~~~~~

    Various mixins for model extension.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import ctx
from inyoka.core.markup.parser import parse, render, RenderContext



class TextRendererMixin(object):
    """A mixin that implements two new properties to access the
    :mod:`inyoka.core.markup` module.

    """

    def get_render_context(self, request=None):
        return RenderContext(request or ctx.current_request)

    def get_render_instructions(self, text, request=None, format='html'):
        instructions = parse(text).compile(format)
        return instructions

    def get_rendered_text(self, text, request=None, format='html'):
        context = self.get_render_context(request)
        instructions = self.get_render_instructions(text, request, format)
        return render(instructions, context)
