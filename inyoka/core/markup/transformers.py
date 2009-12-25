# -*- coding: utf-8 -*-
"""
    inyoka.core.markup.transformers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module holds ast transformers we use.  Transformers can assume that
    they always operate on complete trees, thus the outermost node is always
    a container node.

    Transformers are not necessarily the last thing that processes a tree.
    For example macros that are marked as tree processors and have have their
    stage attribute set to 'final' are expanded after all the transformers
    finished their job.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka import Interface


class ITransformer(Interface):
    """
    Baseclass for all transformers.
    """

    def transform(self, tree):
        """
        This is passed a tree that should be processed.  A class can modify
        a tree in place, the return value has to be the tree then.  Otherwise
        it's safe to return a new tree.
        """
        return tree
