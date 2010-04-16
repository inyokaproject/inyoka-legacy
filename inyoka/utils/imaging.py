# -*- coding: utf-8 -*-
"""
    inyoka.utils.imaging
    ~~~~~~~~~~~~~~~~~~~~

    Imaging related stuff (creating thumbnails,resize images,....).

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.context import ctx


def string_to_xy(string):
    """
    Convert a string `100x50` to a tuple like `(100, 50)`.

    Example Usage::

        >>> string_to_xy(u'100x50')
        (100, 50)

    :param string: A string object.
    :returns: A tuple with (x, y)
    :rtype: Tuple with integers
    """
    return tuple([int(x) for x in string.strip().split(u'x')[:2]])


class BaseImage(object):
    """
    Base class for all imaging related stuff, you never use this class directly.

    Example Usage::

        thumbnail = Image('/tmp/avatar-big.png')
        thumbnail.resize(100, 100)
        thumbnail.save('/tmp/avatar-100-100.png')

    :param filename: Either a filelike object or a filename.
    """

    def __init__(self, filename):
        raise NotImplementedError

    def resize(self, x, y):
        """
        Resizes this image object, you should overwrite this method in
        your own backends. Take a look at PilImage for an example.

        :param x: Destination X resolution
        :param y: Destination Y resolution
        """
        raise NotImplementedError

    def thumbnail(self):
        """
        Resize image to thumbnail size, as definied in inyoka.ini.
        """
        self.resize(*string_to_xy(ctx.cfg["imaging.thumbnailsize"]))

    def avatar(self):
        """
        Resize image to avatar size, as definied in inoka.ini.
        """
        self.resize(*string_to_xy(ctx.cfg["imaging.avatarsize"]))

    def size(self):
        """
        Get the size of this image.

        It is required to override this method on your own backends.

        :return: Imagesize as tuple (width, height)
        """
        raise NotImplementedError

    def save(self, filename, format=None):
        """
        Saves this image object to a new file named `filename`.

        It is required to override this method on your own backends.

        :param filename: Either a filelike object or a filename.
        :param format: The format to save the image if supported by the backend.
        """
        raise NotImplementedError


class PilImage(BaseImage):
    """
    Python Imaging based backend.
    """

    def __init__(self, filename):
        from PIL import Image as PILImage
        self.__antialias = PILImage.ANTIALIAS
        self.image = PILImage.open(filename)

    def resize(self, x, y):
        """Returns a resized copy of an image."""
        self.image = self.image.resize((x, y), self.__antialias)
        return self.image

    def thumbnail(self):
        """
        Resize image to thumbnail size, as definied in inyoka.ini.
        """
        self.image = self.image.thumbnail(string_to_xy(
            ctx.cfg['imaging.thumbnailsize']), self.__antialias)
        return self.image

    def avatar(self):
        """
        Resize image to avatar size, as definied in inoka.ini.
        """
        self.image = self.image.thumbnail(string_to_xy(
            ctx.cfg['imaging.avatarsize']), self.__antialias)
        return self.image

    def size(self):
        return self.image.size

    def save(self, filename, format=None):
        if format:
            self.image.save(filename, format)
        else:
            self.image.save(filename)


class GdkImage(BaseImage):
    """
    Gdk based backend.
    """

    def __init__(self, filename):
        pass

    def resize(self, x, y):
        pass

    def size(self):
        pass

    def save(self, filename):
        pass


# Setup Backend
_backend = ctx.cfg["imaging.backend"]
if _backend == "gdk":
    Image = GdkImage
else:
    Image = PilImage
