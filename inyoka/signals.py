# -*- coding: utf-8 -*-
"""
    inyoka.signals
    ~~~~~~~~~~~~~~

    Implements signals based on blinker.

    :copyright: 2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from blinker import Namespace

#: the namespace for code signals.  If you are not Inyoka code, do
#: not put signals in here.  Create your own namespace instead.
signals = Namespace()
