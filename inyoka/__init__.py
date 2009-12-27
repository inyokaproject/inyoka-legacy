# -*- coding: utf-8 -*-
"""
    inyoka
    ~~~~~~

    The inyoka portal system.  The system is devided into multiple modules
    to which we refer as applications.  The name inyoka means "snake" in
    zulu and was chosen because it's a Python application *cough*.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
from os.path import realpath, dirname, join, pardir
from inspect import getmembers, isclass
from werkzeug import import_string, find_modules, cached_property
from inyoka.core.context import LocalProperty


INYOKA_REVISION = 'unknown'


class InterfaceMeta(type):
    """Metaclass that keeps track of all derived interface implementations."""

    _registry = {}

    def __new__(mcs, classname, bases, dict_):
        obj = type.__new__(mcs, classname, bases, dict_)
        if bases == (object,):
            # `Interface` itself
            return obj

        if Interface in bases:
            # A Interface type
            module = dict_['__module__']
            obj._isinterface = True
            uniquename = module + '.' + classname
            if uniquename in InterfaceMeta._registry:
                raise RuntimeError(u'Interface type with name %r already '
                                   u'exists' % uniquename)
            InterfaceMeta._registry[uniquename] = True
        else:
            # A Interface
            obj._interfaces = interfaces = []
            obj._isinterface = False
            for base in bases:
                if '_isinterface' in base.__dict__:
                    interfaces.append(base)
                elif '_interfaces' in base.__dict__:
                    interfaces.extend(base._interfaces)
        return obj


class Interface(object):
    """Base Interface class.

    A interface is some kind of functionality provider that needs to
    be subclassed to implement the real features.

    That way a :class:`Interface` can keep track of all subclasses and
    thanks to that knows all implemented “features” for that kind of Interface.

    """
    __metaclass__ = InterfaceMeta

    def __init__(self, ctx=None):
        self.ctx = ctx


def _is_interface(value):
    _registry = InterfaceMeta._registry
    return (isclass(value) and issubclass(value, Interface) and
            value is not Interface)


def _import_modules(modules):
    # Import the components to setup the metaclass magic.
    for module in modules:
        # No star at the end means a package/module/class but nothing below.
        if module[-1] != '*':
            yield import_string(module)
        else:
            try:
                for mod in find_modules(module[:-2], True, True):
                    yield import_string(mod)
            except ValueError: # module is a module and not a package
                yield import_string(module[:-2])


class ApplicationContext(object):
    """Overall application context for Inyoka.

    This class acts as a wrapper for the whole Inyoka component system.
    It is used to keep track of all components, to load or unload them
    and to manage the thread-locals.

    Next to that the :class:`ApplicationContext` is the real WSGI-Application
    and only wraps :class:`~inyoka.dispatcher.RequestDispatcher` for
    dispatching purposes.
    """

    def __init__(self):
        #: Interface type -> classes mapping
        self._components = {}
        #: component class -> instance mapping
        self._instances = {}

        # setup config
        from inyoka.core.config import Configuration
        cfile = os.environ.get('INYOKA_CONFIG', 'inyoka.ini')
        self.cfg = cfg = Configuration(join(realpath(
            os.environ['INYOKA_INSTANCE']), cfile
        ))

        if not cfg.exists:
            trans = cfg.edit()
            trans.commit(force=True)
            cfg.touch()

    def bind(self):
        """This method binds the :class:`ApplicationContext` to
        our thread-local so that all components can access it.
        """
        from inyoka.core.context import local
        local.ctx = self

    @cached_property
    def dispatcher(self):
        from inyoka.dispatcher import make_dispatcher
        return make_dispatcher(self)

    #: The current request in the thread-local
    current_request = LocalProperty('request')

    def load_component(self, component):
        """Load a component.

        :param component: A component object.  This must be an
                          an implementation not an interface to get loaded.
        """
        try:
            for interface in component._interfaces:
                self._components.setdefault(interface, []).append(component)
        except (AttributeError, TypeError):
            # fail silently if we try to register an interface but raise
            # if there's something completely wrong
            if not hasattr(component, '_isinterface'):
                raise RuntimeError(u'Type %r is not a component' % component)
        else:
            return component

    def load_components(self, components):
        """Load various components, see
        :meth:`~ApplicationContext.load_component` for more details.
        """
        ret = []
        for component in components:
            loaded = self.load_component(component)
            if loaded:
                ret.append(loaded)
        return ret

    def unload_components(self, components):
        """Remove various components from the context.

        :param components:  A list of components to unload.
        """
        unloaded = []
        for component in components:
            try:
                if getattr(component, '_isinterface', False):
                    unloaded.append(self._components.pop(component))
            except:
                # fail silently if component is not loaded
                continue

    def load_packages(self, packages):
        """Load all components from a known python package.

        Example::

            ctx.load_packages(['inyoka.core.*'])

        This loads recursivly all packages found in :mod:`inyoka.core`.

        :param packages:  A list of strings of import paths.
        :returns: A list of loaded component classes.
        """
        modules = _import_modules(packages)
        components = list(m[1] for m in
            sum((getmembers(mod, _is_interface) for mod in modules), [])
        )
        return self.load_components(components)

    def get_implementations(self, interface, instances=False):
        """Return all known implementations of `interface`.

        :param interface: The interface all implementations need to implement
        :param instances: Return all implementations as instances not classes.

        """
        if not instances:
            return self._components.get(interface, ())
        return [self.get_instance(impl) for impl in
                self._components.get(interface, ())]

    def get_instance(self, compcls):
        """Return the instance of a component class.
        If a component was not yet accessed by instance it is instanciated
        instantly.
        """
        if compcls not in self._instances:
            self._instances[compcls] = compcls(self)
        return self._instances[compcls]

    def __call__(self, environ, start_response):
        retval = self.application(environ, start_response)
        # rebind everything to the thread local
        self.bind()
        return retval


def _bootstrap():
    """Get the inyoka version and store it."""
    global INYOKA_REVISION
    from subprocess import Popen, PIPE

    # get inyoka revision
    hg = Popen(['hg', 'tip'], stdout=PIPE, stderr=PIPE, stdin=PIPE,
               cwd=os.path.dirname(__file__))
    hg.stdin.close()
    hg.stderr.close()
    rev = hg.stdout.read()
    hg.stdout.close()
    hg.wait()
    hg_node = None
    if hg.wait() == 0:
        for line in rev.splitlines():
            bucket = line.split(':', 1)
            if len(bucket) == 2 and bucket[0].lower().strip() == 'changeset':
                hg_node = bucket[1].strip()
                break
    INYOKA_REVISION = hg_node

    # the path to the contents of the inyoka module
    os.environ.setdefault('INYOKA_MODULE', realpath(join(dirname(__file__))))
    conts = os.environ['INYOKA_MODULE']
    # the path to the inyoka instance folder
    os.environ.setdefault('INYOKA_INSTANCE', realpath(join(conts, pardir)))

    #: bind the context
    ctx = ApplicationContext()
    ctx.bind()


    # setup components
    test_components = []
    if ctx.cfg['debug']:
        test_components = [
            'tests.core.test_database.*',
            'tests.core.test_subscriptions.*',
            'tests.utils.*',
        ]

    # TODO: make it configurable
    ctx.load_packages([
        'inyoka.testing.*',
        'inyoka.core.*',
        'inyoka.admin.*',
        'inyoka.portal.*',
        'inyoka.news.*',
        'inyoka.forum.*',
        'inyoka.paste.*',
    ] + test_components)

    # setup model property providers
    from inyoka.core.database import (IModelPropertyProvider, DeclarativeMeta,
                                      ModelPropertyProviderGoesWild)

    property_providers = ctx.get_implementations(IModelPropertyProvider)
    extendable_models = [m for m in DeclarativeMeta._models
                         if getattr(m, '__extendable__', False)]
    for model in extendable_models:
        for provider in property_providers:
            if provider.model is not model:
                continue

            for key, value in provider.properties.iteritems():
                if key not in model.__dict__:
                    setattr(model, key, value)
                else:
                    raise ModelPropertyProviderGoesWild(
                        u'%r tried to overwrite already existing '
                        u'properties on %r, aborting'
                            % (provider, model))

_bootstrap()
del _bootstrap
