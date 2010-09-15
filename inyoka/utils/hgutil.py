# -*- coding: utf-8 -*-
"""
    inyoka.utils.hgutil
    ~~~~~~~~~~~~~~~~~~~

    Utility module to interact with mercurial.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from mercurial import ui as hgui
from mercurial import commands as hgcmd


class iui(hgui.ui):

    def __init__(self, *args, **kwargs):
        hgui.ui.__init__(self, *args, **kwargs)
        self._output = []

    def get_output(self):
        return u''.join(self._output)

    def write(self, *args, **kwargs):
        """Simple overwrite that returns the output as a string"""
        self._output.extend(args)
