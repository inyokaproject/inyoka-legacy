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
from inyoka.core.i18n import lazy_gettext
from inyoka.core.environ import PACKAGE_LOCATION, MEDIA_DATA

#### TODO: Cleanup validation

class ConfigField(object):
    def __init__(self, default, help_text):
        self.default = default
        self.help_text = help_text

    get_default = lambda self: self.default
    converter = lambda self: self.default

    def __call__(self, value):
        return self.converter(value)

class IntegerField(ConfigField):
    converter = int

class TextField(ConfigField):
    def converter(self, value):
        if isinstance(value, unicode):
            return value.strip()
        else:
            return value.decode('utf-8').strip()

class BooleanField(ConfigField):
    def converter(self, value):
        if isinstance(value, (str, unicode)):
            if value.lower() in ('yes', 'y', 'true', '1'):
                return True
        else:
            return bool(value)

        return False


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

def from_string(value, field):
    """Try to convert a value from string or fall back to the default."""
    try:
        return field(value)
    except ValidationError, e:
        return field.get_default()


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

        from inyoka.core.config.defaults import DEFAULTS
        self.config_vars = DEFAULTS.copy()
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
            field = self.config_vars[key]
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
            return self.cfg.config_vars[key].value
        return self.cfg[key]

    def __setitem__(self, key, value):
        """Set the value for a key by a python value."""
        self._assert_uncommitted()

        if value == self[key]:
            return
        if key not in self.cfg.config_vars:
            raise KeyError(key)
        if isinstance(value, str):
            value = value.decode('utf-8')
        field = self.cfg.config_vars[key]
        self._values[key] = field(value)
        self._converted_values[key] = value

    def _assert_uncommitted(self):
        if self._committed:
            raise ValueError('This transaction was already committed.')

    def set_from_string(self, key, value, override=False):
        """Set the value for a key from a string."""
        self._assert_uncommitted()
        field = self.cfg.config_vars[key]
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
                    section, key = key.split('.', 1)
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


config = Configuration(path.join(PACKAGE_LOCATION, 'inyoka.ini'))
