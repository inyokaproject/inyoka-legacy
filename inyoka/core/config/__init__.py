# -*- coding: utf-8 -*-
"""
    inyoka.core.config
    ~~~~~~~~~~~~~~~~~~

    This module implements the configuration.  The configuration is a more or
    less flat thing saved as ini in the instance folder.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""
import os
from os import path
from threading import Lock
from wtforms.validators import ValidationError
from markupsafe import soft_unicode
from blinker import signal
from io import open


DEFAULTS = {}

_quote_table = {
    ord('\\'): u'\\\\',
    ord('\n'): u'\\n',
    ord('\r'): u'\\r',
    ord('"'): u'\\"'
}


class ConfigField(object):
    """A field representing a configuration entry.

    To create your own field types subclass and override
    :meth:`converter` to match your needs.
    """

    def __init__(self, name, default):
        self.default = default
        # Register that field only if ’name’ is not ’None’.
        # This makes it easy to create new fields for unittesting
        # or to play around in the interactive shell.
        if name is not None:
            self.__name__ = name
            Configuration.defined_vars[name] = self

    def get_default(self):
        return self.default

    def converter(self, value=None):
        return self.get_default()

    def __call__(self, value=None):
        return self.converter(value)


class IntegerConfigField(ConfigField):
    """A field representing integer values"""

    def __init__(self, name, default, min_value=-1):
        ConfigField.__init__(self, name, default)
        self.min_value = min_value

    def converter(self, value=None):
        """Convert values to int and assure that we regard
        the minimum value
        """
        if value < self.min_value:
            return int(self.min_value)
        else:
            return int(value)


class TextConfigField(ConfigField):
    """A field representing unicode values"""

    def converter(self, value=None):
        """Convert values to stripped unicode values"""
        return soft_unicode(value).strip()


class DottedConfigField(ConfigField):
    """A field representing many values but at least two.
    This converter only fixes values that does not contain
    a doublepoint so applications can safely split on it.

    """

    def converter(self, value=None):
        if ':' not in value:
            value = ':' + value
        return value


class ListConfigField(ConfigField):
    """A field representing a list. The list can contain any other supported
    data type. `:` is used as a separator character between the items.
    """

    def __init__(self, name, default, field=None):
        ConfigField.__init__(self, name, default)
        if field is not None:
            self.conversion_field = field
        else:
            self.conversion_field = TextConfigField(u'', u'')

    def converter(self, value=None):
        if not isinstance(value, basestring):
            return value
        erg = []
        for value in value.split(':'):
            erg.append(self.conversion_field(value))
        return erg


class BooleanConfigField(ConfigField):
    """A field representing boolean values"""

    TRUE_STATES = ['1', 'yes', 'true', 'on']
    FALSE_STATES = ['0', 'no', 'false', 'off']

    def converter(self, value=None):
        if isinstance(value, basestring):
            if value.lower() in BooleanConfigField.TRUE_STATES:
                return True
            elif value.lower() in BooleanConfigField.FALSE_STATES:
                return False
        else:
            return bool(value)

        return False


#: header for the config file
CONFIG_HEADER = u'# Generated Configuration file\n'


def unquote_value(value):
    """Unquote a configuration value."""
    if not value:
        return ''
    if value[0] in '"\'' and value[0] == value[-1]:
        value = value[1:-1].decode('string-escape')
    return soft_unicode(value)


def quote_value(value):
    """Quote a configuration value.

    Takes either an bytestring or unicode and returns
    an escaped utf-8 encoded bytestring.
    """
    if isinstance(value, bool):
        value = u'1' if value else u'0'
    if isinstance(value, (int, long)):
        value = unicode(value)
    if isinstance(value, list):
        value = u':'.join(value)

    if not value:
        return ''
    if value.strip() == value and value[0] not in '"\'' and \
       value[-1] not in '"\'' and len(value.splitlines()) == 1:
        return value.encode('utf-8')
    return (u'"%s"' % value.translate(_quote_table)).encode('utf-8')


#TODO: Right now this funtion does not work since our `convert` methods
#      do not raise `ValidationError`.  The validation behaviour needs
#      to be rewritten somehow to store information about misconfigured
#      values.  The easiest way would be to provide a funtion that does
#      not fallback, so that that one can be used in the UI to set config
#      values.
def from_string(value, field):
    """Try to convert a value from string or fall back to the default."""
    try:
        return field(value)
    except ValidationError:
        return field.get_default()


class Configuration(object):
    """Helper class that manages configuration values in a INI configuration
    file.
    """

    reload_signal = signal('config-changed',
        u'This signal will be emitted everytime the configuration will go'
        u' through the reloading process')

    defined_vars = {}

    def __init__(self, filename, defaults=None):
        self.filename = filename
        self._values = {}
        self._converted_values = {}
        self._lock = Lock()
        with self._lock:
            self._load_config()

    def _load_config(self):
        # if the path does not exist yet set the existing flag to none and
        # set the time timetamp for the filename to something in the past
        if not path.exists(self.filename):
            self.exists = False
            self._load_time = 0
            return

        # otherwise parse the file and copy all values into the internal
        # values dict.  Do that also for values not covered by the current
        # `defined_vars` dict to preserve variables of disabled plugins
        self._load_time = path.getmtime(self.filename)
        self.exists = True
        section = 'inyoka'
        with open(self.filename) as fobj:
            for line in fobj:
                line = line.strip()
                if not line or line[0] in '#;':
                    continue
                elif line[0] == '[' and line[-1] == ']':
                    section = line[1:-1].strip()
                    section = section.rstrip(u'.')
                elif '=' not in line:
                    key = line.strip()
                    value = ''
                else:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    if section != 'inyoka':
                        if not section.endswith('.'):
                            section += '.'
                        key = section + key
                    self._values[key] = unquote_value(value.strip())

    def __getitem__(self, key):
        """Return the value for a key."""
        try:
            return self._converted_values[key]
        except KeyError:
            field = self.defined_vars[key]
        try:
            value = from_string(self._values[key], field)
        except KeyError:
            value = field.get_default()
        self._converted_values[key] = value
        return value

    def __setitem__(self, key, value):
        """Set the config item's value.
        May raise `IOError`, you may want to use `change_single`."""
        self.change_single(key, value, False)

    def __delitem__(self, key):
        """Revert the config item's value to its default.
        May raise `IOError`, you may want to use `revert_single`"""
        self.revert_single(key, False)

    def change_single(self, key, value, silent=False):
        """Create and commit a transaction fro a single key-value pair.

        Return `True` on success, otherwise `False`.  If :attr:`silent` is
        applied `True` we fail silently on exceptions.
        """
        trans = self.edit()
        try:
            trans[key] = value
            trans.commit()
        except IOError:
            if silent:
                return False
            raise
        return True

    def revert_single(self, key, silent=False):
        """Revert a single key to it's default.

        Fail silently if :attr:`silent` is applied `True`,
        see :meth:`change_single` for more details.
        """
        trans = self.edit()
        try:
            trans.revert_to_default(key)
            trans.commit()
        except IOError:
            if silent:
                return False
            raise
        return True

    def edit(self):
        """Return a new transaction object."""
        return ConfigTransaction(self)

    def touch(self):
        """Touch the file to trigger a reload."""
        os.utime(self.filename, None)

    def reload(self):
        with self._lock:
            self._values = {}
            self._converted_values = {}
            self._load_config()
        Configuration.reload_signal.send('config-changed', config=self)
        return self

    @property
    def changed_external(self):
        """True if there are changes on the file system."""
        if not path.isfile(self.filename):
            return False
        return path.getmtime(self.filename) > self._load_time

    def __iter__(self):
        """Iterate over all keys"""
        return iter(self.defined_vars)

    iterkeys = __iter__

    def __contains__(self, key):
        """Check if a given key exists."""
        return key in self.defined_vars

    def itersection(self, section):
        """Iterate over all values."""
        for key in self:
            if key.startswith(section):
                yield key, self[key]

    def itervalues(self, section=None):
        """Iterate over all values."""
        for key in self.iterkeys():
            yield self[key]

    def iteritems(self):
        """Iterate over all keys and values."""
        for key in self:
            yield key, self[key]

    def values(self):
        """Return a list of values."""
        return list(self.itervalues())

    def keys(self):
        """Return a list of keys."""
        return list(self)

    def items(self):
        """Return a list of all key, value tuples."""
        return list(self.iteritems())

    def __len__(self):
        return len(self.defined_vars)

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, dict(self.items()))


class ConfigTransaction(object):
    """A configuration transaction class. Instances of this class are returned
    by Config.edit(). Changes can then be added to the transaction and
    eventually be committed and saved to the file system using the commit()
    method.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self._values = {}
        self._converted_values = {}
        self._remove = []
        self._committed = False

    def __getitem__(self, key):
        """Get an item from the transaction or the underlaying config."""
        if key in self._converted_values:
            return self._converted_values[key]
        elif key in self._remove:
            return self.cfg.defined_vars[key].value
        return self.cfg[key]

    def __setitem__(self, key, value):
        """Set the value for a key by a python value."""
        self._assert_uncommitted()
        if value == self[key]:
            return
        if key not in self.cfg.defined_vars:
            raise KeyError(key)
        if isinstance(value, str):
            value = unicode(value, 'utf-8')

        field = self.cfg.defined_vars[key]
        self._values[key] = field(value)
        self._converted_values[key] = value

    def _assert_uncommitted(self):
        if self._committed:
            raise ValueError('This transaction was already committed.')

    def set_from_string(self, key, value, override=False):
        """Set the value for a key from a string."""
        self._assert_uncommitted()
        field = self.cfg.defined_vars[key]
        new = from_string(value, field)
        old = self._converted_values.get(key, None) or self.cfg[key]
        if override or unicode(old) != unicode(new):
            self[key] = new

    def revert_to_default(self, key):
        """Revert a key to the default value."""
        self._assert_uncommitted()
        if key.startswith('inyoka'):
            key = key[11:]
        self._remove.append(key)

    def update(self, *args, **kwargs):
        """Update multiple items at once."""
        for key, value in dict(*args, **kwargs).iteritems():
            self[key] = value

    def commit(self, force=False):
        """Commit the transactions. This first tries to save the changes to the
        configuration file and only updates the config in memory when that is
        successful.
        """
        self._assert_uncommitted()
        if not self._values and not self._remove and not force:
            self._committed = True
            return
        self.cfg._lock.acquire()
        try:
            all = self.cfg._values.copy()
            all.update(self._values)
            for key in self._remove:
                all.pop(key, None)

            sections = {}
            for key, value in all.iteritems():
                if '.' in key:
                    splitted = key.split('.')
                    section = u'.'.join(splitted[:-1])
                    key = splitted[-1]
                else:
                    section = 'inyoka'
                sections.setdefault(section, []).append((key, value))
            sections = sorted(sections.items())
            for section in sections:
                section[1].sort()

            with open(self.cfg.filename, 'w') as fobj:
                fobj.write(CONFIG_HEADER)
                for idx, (section, items) in enumerate(reversed(sections)):
                    if idx:
                        fobj.write(u'\n')
                    fobj.write(u'[%s]\n' % section)
                    for key, value in items:
                        fobj.write(u'%s = %s\n' % (key, quote_value(value)))
            self.cfg._values.update(self._values)
            self.cfg._converted_values.update(self._converted_values)
            for key in self._remove:
                self.cfg._values.pop(key, None)
                self.cfg._converted_values.pop(key, None)
        finally:
            self.cfg._lock.release()
        self._committed = True
