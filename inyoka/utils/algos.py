from hashlib import sha1

def get_hexdigest(salt, raw_password):
    """
    Returns a string of the hexdigest of the given plaintext password and salt
    using the sha1 algorithm.
    """
    if isinstance(raw_password, unicode):
        raw_password = raw_password.encode('utf-8')
    return sha1(str(salt) + raw_password).hexdigest()

