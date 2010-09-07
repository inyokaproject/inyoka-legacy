# -*- coding: utf-8 -*-
"""
    inyoka.utils.imaging
    ~~~~~~~~~~~~~~~~~~~~

    Imaging related stuff (creating thumbnails,resize images,....).

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.context import ctx
from inyoka.utils.decorators import abstract
from inyoka.utils.datastructures import OrderedDict

# Try to import PyGame
try:
    import pygame
except ImportError:
    pass

# Try to import PIL
try:
    from PIL import Image as PilBackend
except ImportError:
    pass


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


class NoBackendFound(Exception):
    """This exceptions is raised once we cannot find a suitable backend"""
    pass


class BaseImage(object):
    """
    Base class for all imaging related stuff, you never use this class directly.

    Example Usage::

        thumbnail = Image('/tmp/avatar-big.png')
        thumbnail.resize(100, 100)
        thumbnail.save('/tmp/avatar-100-100.png')

    :param filename: Image filename
    """

    def __init__(self, filename):
        raise NotImplementedError

    @classmethod
    def init(cls):
        """
        A beautifull way to load class dependecies like python modules and
        global configuration things.

        You should overwrite this method if your own instance needs some
        more python modules. If your imaging backend only uses things like
        os.Popen() you should move these imports to the global namespace
        instead.

        This method must return either `True` or `False` describing whether
        it's loaded or not.  This method must not raise exceptions!
        """
        return cls

    @abstract
    def scale(self, x, y):
        """
        Resizes this image object, you should overwrite this method in
        your own backends. Take a look at :class:`PilImage` for an example.

        :param x: Destination X resolution
        :param y: Destination Y resolution
        """

    def thumbnail(self):
        """
        Resize image to thumbnail size, as definied in inyoka.ini.
        """
        self.scale(*string_to_xy(ctx.cfg["imaging.thumbnailsize"]))

    def avatar(self):
        """
        Resize image to avatar size, as defined in inyoka.ini.
        """
        self.scale(*string_to_xy(ctx.cfg["imaging.avatarsize"]))

    @abstract
    def size(self):
        """
        Get the size of this image.

        It is required to override this method on your own backends.

        :return: Imagesize as tuple (width, height)
        """

    @abstract
    def save(self, filename):
        """
        Saves this image object to a new file named `filename`.

        It is required to override this method on your own backends.

        :param filename: Either a filelike object or a filename.
        """
        raise NotImplementedError


class PilImage(BaseImage):
    """
    Python Imaging based backend.
    """

    def __init__(self, filename):
        self.image = PilBackend.open(filename)

    @classmethod
    def init(cls):
        return 'PilBackend' in globals()

    def scale(self, x, y):
        self.image = self.image.resize((x, y), PilBackend.ANTIALIAS)

    def size(self):
        return self.image.size

    def save(self, filename):
        self.image.save(filename)


class PyGameImage(BaseImage):
    """
    PyGame based imaging backend.
    """

    def __init__(self, filename):
        self.image = pygame.image.load(filename)

    @classmethod
    def init(cls):
        return 'pygame' in globals()

    def scale(self, x, y):
        self.image = pygame.transform.smoothscale(self.image, (x, y))

    def size(self):
        return self.image.get_size()

    def save(self, filename):
        pygame.image.save(self.image, filename)


# backends ordered by priority.  The higher the faster
# the backend, keep it sorted!
BACKENDS = OrderedDict([
    ('pygame', PyGameImage),
    ('pil', PilImage),
])

def get_imaging_backend(name=None):
    if name:
        try:
            return BACKENDS[name]
        except KeyError:
            raise NoBackendFound(u'Backend %s is not available. '
                u'Available backends: %s' % (name, u', '.join(BACKENDS.keys()))
            )
    for backend in BACKENDS.itervalues():
        if backend.init():
            return backend
    raise NoBackendFound(u'No suitable backend found, please install the dependencies!')
