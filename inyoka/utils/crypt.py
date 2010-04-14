# -*- coding: utf-8 -*-
"""
    inyoka.utils.crypt
    ~~~~~~~~~~~~~~~~~~

    Various utilties for cryptographic tasks

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from hashlib import sha1


def get_hexdigest(salt, raw_password):
    """
    Returns a string of the hexdigest of the given plaintext password and salt
    using the sha1 algorithm.
    """
    if isinstance(raw_password, unicode):
        raw_password = raw_password.encode('utf-8')
    return sha1(str(salt) + raw_password).hexdigest()
