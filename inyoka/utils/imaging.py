# -*- coding: utf-8 -*-
"""
    inyoka.utils.imaging
    ~~~~~~~~~~~~~~~~~~~~

    Imaging realted stuff (creating thumbnails,resize images,....).

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

class BaseImage(object):
    """

    :param filename: Either a filelike object or a filename.
    """

    def __init__(self, filename):
        pass

    def resize(self, x, y):
        """

        :param x: Destination X resolution
        :param y: Designation Y resolution
        """
        pass

    def thumbnail(self):
        """
        """
        pass

    def avatar(self):
        """
        """
        pass

    def save(self, filename):
        """

        :param filename: Either a filelike object or a filename.
        """
        pass
