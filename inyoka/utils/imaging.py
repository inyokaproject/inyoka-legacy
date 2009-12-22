# -*- coding: utf-8 -*-
"""
    inyoka.utils.imaging
    ~~~~~~~~~~~~~~~~~~~~

    Imaging related stuff (creating thumbnails,resize images,....).

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

class BaseImage(object):
    """
    Base class for all imaging related stuff, you never use this class directly.

    Example Usage:
        >>> thumbnail = Image('/tmp/avatar-big.png')
        >>> thumbnail.resize(100,100)
        >>> thumbnail.save('/tmp/avatar-100-100.png')

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
        Resize image to thumbnail size, as definied in inyoka.ini.
        """
        pass

    def avatar(self):
        """
        Resize image to avatar size, as definied in inoka.ini.
        """
        pass

    def size(self):
        """
        Get the size of this image.

        :return: Imagesize as tuple (width, height)
        """
        pass

    def save(self, filename):
        """
        Saves this image object to a new file named `filename`.

        :param filename: Either a filelike object or a filename.
        """
        pass
