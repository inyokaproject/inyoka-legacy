# -*- coding: utf-8 -*-
"""
    inyoka.config
    ~~~~~~~~~~~~~

    This module implements the configuration.  The configuration is a more or
    less flat thing saved as ini in the instance folder.  If the configuration
    changes the application is reloaded automatically.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: MIT
"""
from __future__ import with_statement
import os
from os import path
from threading import Lock

#XXX: This is just for development reasons.  If we get something usable
#     that variable should move into some kind of setup process.
DEFAULTS = {
}


#: header for the config file
CONFIG_HEADER = '# Generated Configuration file\n'


def config_overriding_val(app, default, default_arg, config_key, config_type):
    """A value that is overriden with a default, and from the config"""
    if default_arg is not None:
        default = default_arg
    app.add_config_var(config_key, config_type, default)
    value = app.cfg[config_key]
    return value


def unquote_value(value):
    """Unquote a configuration value."""
    if not value:
        return ''
    if value[0] in '"\'' and value[0] == value[-1]:
        value = value[1:-1].decode('string-escape')
    return value.decode('utf-8')


def quote_value(value):
    """Quote a configuration value."""
    if not value:
        return ''
    if value.strip() == value and value[0] not in '"\'' and \
       value[-1] not in '"\'' and len(value.splitlines()) == 1:
        return value.encode('utf-8')
    return '"%s"' % value.replace('\\', '\\\\') \
                         .replace('\n', '\\n') \
                         .replace('\r', '\\r') \
                         .replace('\t', '\\t') \
                         .replace('"', '\\"').encode('utf-8')


def from_string(value, conv, default):
    """Try to convert a value from string or fall back to the default."""
    if conv is bool:
        conv = lambda x: x == 'True'
    try:
        return conv(value)
    except (ValueError, TypeError), e:
        return default


def get_converter_name(conv):
    """Get the name of a converter"""
    return {
        bool:   'boolean',
        int:    'integer',
        float:  'float',
    }.get(conv, 'string')


class Configuration(object):
    """Helper class that manages configuration values in a INI configuration
    file.
    """

    def __init__(self, filename, namespace=None):
        self.filename = filename
        self.namespace = {}
        self.namespace.update(namespace) if namespace is not None else namespace

        self.config_vars = DEFAULT.copy()
        self._values = {}
        self._converted_values = {}
        self._lock = Lock()

        # if the path does not exist yet set the existing flag to none and
        # set the time timetamp for the filename to something in the past
        if not path.exists(self.filename):
            self.exists = False
            self._load_time = 0
            return

        # otherwise parse the file and copy all values into the internal
        # values dict.  Do that also for values not covered by the current
        # `config_vars` dict to preserve variables of disabled plugins
        self._load_time = path.getmtime(self.filename)
        self.exists = True
        section = 'inyoka'
        with file(self.filename) as fobj:
            for line in fobj:
                line = line.strip()
                if not line or line[0] in '#;':
                    continue
                elif line[0] == '[' and line[-1] == ']':
                    section = line[1:-1].strip()
                elif '=' not in line:
                    key = line.strip()
                    value = ''
                else:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    if section != 'inyoka':
                        key = section + '/' + key
                    self._values[key] = unquote_value(value.strip())

    def __getitem__(self, key):
        """Return the value for a key."""
        try:
            return self._converted_values[key]
        except KeyError:
            conv, default = self.config_vars[key]
        try:
            value = from_string(self._values[key], conv, default)
        except KeyError:
            value = default
        self._converted_values[key] = value
        return value

    def change_single(self, key, value):
        """Create and commit a transaction for a single key-value-pair. Return
        True on success, otherwise False.
        """
        t = self.edit()
        t[key] = value
        try:
            t.commit()
            return True
        except IOError:
            return False

    def edit(self):
        """Return a new transaction object."""
        return ConfigTransaction(self)

    def touch(self):
        """Touch the file to trigger a reload."""
        os.utime(self.filename, None)

    @property
    def changed_external(self):
        """True if there are changes on the file system."""
        if not path.isfile(self.filename):
            return False
        return path.getmtime(self.filename) > self._load_time

    def __iter__(self):
        """Iterate over all keys"""
        return iter(self.config_vars)

    iterkeys = __iter__

    def __contains__(self, key):
        """Check if a given key exists."""
        return key in self.config_vars

    def itervalues(self):
        """Iterate over all values."""
        for key in self:
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
        return len(self.config_vars)

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
            return self.cfg.config_vars[key][1]
        return self.cfg[key]

    def __setitem__(self, key, value):
        """Set the value for a key by a python value."""
        self._assert_uncommitted()
        if key not in self.cfg.config_vars:
            raise KeyError(key)
        if isinstance(value, str):
            value = value.decode('utf-8')
        if value == self.cfg.config_vars[key][1]:
            self._remove.append(key)
        else:
            self._values[key] = unicode(value)
            self._converted_values[key] = value

    def _assert_uncommitted(self):
        if self._committed:
            raise ValueError('This transaction was already committed.')

    def set_from_string(self, key, value, override=False):
        """Set the value for a key from a string."""
        self._assert_uncommitted()
        conv, default = self.cfg.config_vars[key]
        new = from_string(value, conv, default)
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

    def commit(self):
        """Commit the transactions. This first tries to save the changes to the
        configuration file and only updates the config in memory when that is
        successful.
        """
        self._assert_uncommitted()
        if not self._values and not self._remove:
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
                if '/' in key:
                    section, key = key.split('/', 1)
                else:
                    section = 'inyoka'
                sections.setdefault(section, []).append((key, value))
            sections = sorted(sections.items())
            for section in sections:
                section[1].sort()

            f = file(self.cfg.filename, 'w')
            f.write(CONFIG_HEADER)
            try:
                for idx, (section, items) in enumerate(sections):
                    if idx:
                        f.write('\n')
                    f.write('[%s]\n' % section.encode('utf-8'))
                    for key, value in items:
                        f.write('%s = %s\n' % (key, quote_value(value)))
            finally:
                f.close()
            self.cfg._values.update(self._values)
            self.cfg._converted_values.update(self._converted_values)
            for key in self._remove:
                self.cfg._values.pop(key, None)
                self.cfg._converted_values.pop(key, None)
        finally:
            self.cfg._lock.release()
        self._committed = True
