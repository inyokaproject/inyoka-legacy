# -*- coding: utf-8 -*-
"""
    inyoka.core.datastructures
    ~~~~~~~~~~~~~~~~~~

    Datastructures used for many Things to avoid duplicate code.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

class BidiMap(dict):
    """
    A simpler API for simple Bidirectional Mappings.
    """
    
    def __init__(self,items={}):
        """
        Constructor

        items must be a Dict like Object, where keys are Integers.
        """
        dict.__init__(self,**items)
        self.reverse = dict((v,k) for k,v in self.items())

    def __getitem__(self,key):
        """
        Implement object[item] Access to this Class.
        """
        if type(key) == int:
            return dict.__getitem__(self, key)
        else:
            return self.reverse[key]
