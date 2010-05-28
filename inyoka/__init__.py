# -*- coding: utf-8 -*-
"""
    inyoka
    ~~~~~~

    The Inyoka portal system.  The system is devided into multiple modules
    to which we refer as applications.  The name Inyoka means “snake” in
    Zulu and was chosen because it's an application written in Python *cough*.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import re
from os.path import realpath, dirname, join, pardir
from inspect import getmembers, isclass
from werkzeug import find_modules, import_string, cached_property
from inyoka.core.context import LocalProperty


#: Inyoka revision present in the current mercurial working copy
INYOKA_REVISION = 'unknown'


class InterfaceMeta(type):
    """Metaclass that keeps track of all derived interface implementations.

    It touches interfaces and components.  If it registers a new interface it
    will add a new key to :attr:`~inyoka.InterfaceMeta._registry`.

    If an class is an iterface it will set an :attr:`Interface._isinterface`
    attribute to `True` if it's a component to `False`.

    A component has an attribute called :attr:`_interfaces` with all interfaces
    listed the component implements.
    """

    _registry = list()

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
            InterfaceMeta._registry.append(uniquename)
        else:
            # A Interface
            obj._isinterface = False
            # store all unique interfaces
            #XXX: yet for python 2.5 compatibility, upgrade to 2.6 asap to get
            #     cool new things!
            obj._interfaces = set(cls for cls in
                sum(map(lambda obj: obj.mro(), bases), [])
                if '_isinterface' in cls.__dict__)

#            obj._interfaces = set(
#                cls for cls in sum(map(methodcaller('mro'), bases), [])
#                    if '_isinterface' in cls.__dict__
#            )

        return obj


class Interface(object):
    """Base Interface class.

    An interface is some kind of functionality provider that needs to
    be subclassed to implement the real features.

    That way a :class:`Interface` can keep track of all subclasses and
    thanks to that knows all implemented “features” for that kind of interface.

    :param ctx: The current :class:`ApplicationContext`.
    """
    __metaclass__ = InterfaceMeta

    def __init__(self, ctx=None):
        self.ctx = ctx


def _is_interface(value):
    """Determine if a class is an interface"""
    return (isclass(value) and issubclass(value, Interface) and
            value is not Interface)


def _import_modules(modules):
    """Import the components to setup the metaclass magic."""
    for module in modules:
        # No star at the end means a package/module/class but nothing below.
        if module[-1] != '*':
            yield import_string(module)
        else:
            try:
                for mod in find_modules(module[:-2], True, True):
                    yield import_string(mod)
                # find_modules does import our package, but doesn't yield it
                # hence we import it ourself.
                yield import_string(module[:-2])
            except ValueError: #pragma: no cover
                # module is a module and not a package
                yield import_string(module[:-2])


class ApplicationContext(object):
    """Overall application context for Inyoka.

    This class acts as a wrapper for the whole Inyoka component system.
    It is used to keep track of all components, to load or unload them
    and to manage the thread-locals.

    Next to that the :class:`ApplicationContext` is used to represent the real
    WSGI-Application interface.
    It does not implement any proper dispatching or WSGI stack but wraps
    :class:`~inyoka.dispatcher.RequestDispatcher` for that purpose.
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
                self._components.setdefault(interface, set()).add(component)
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
        ret = set()
        for component in set(components):
            loaded = self.load_component(component)
            if loaded:
                ret.add(loaded)
        return ret

    def unload_components(self, components):
        """Remove various components from the context.

        :param components:  A list of components to unload.
        """
        for component in set(components):
            try:
                if getattr(component, '_isinterface', False):
                    self._components.pop(component)
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
        return set([self.get_instance(impl) for impl in
                    self._components.get(interface, ())])

    def get_instance(self, compcls):
        """Return the instance of a component class.
        If a component was not yet accessed by instance it is instanciated
        instantly.
        """
        if compcls not in self._instances:
            self._instances[compcls] = compcls(self)
        return self._instances[compcls]

    def __call__(self, environ, start_response): #pragma: no cover
        """Wrap the WSGI stack.  This only forwards to the respective dispatcher"""
        return self.dispatcher(environ, start_response)


def _bootstrap():
    """Get the Inyoka version and store it."""
    global INYOKA_REVISION
    from subprocess import Popen, PIPE

    # get Inyoka revision
    hg = Popen(['hg', 'id', '-i', '-n'], stdout=PIPE, stderr=PIPE,
               stdin=PIPE, cwd=os.path.dirname(__file__))
    hg.stdin.close()
    hg.stderr.close()
    rev = hg.stdout.readline()
    hg.stdout.close()
    if hg.wait() == 0:
        m = re.match('^(?P<id>[0-9a-z]+)(?P<mod>\+?) (?P<num>[0-9]+)\+?$',
                     rev)
        if m:
            INYOKA_REVISION = '%(num)s:%(id)s%(mod)s' % m.groupdict()

    # the path to the contents of the Inyoka module
    os.environ.setdefault('INYOKA_MODULE', realpath(join(dirname(__file__))))
    conts = os.environ['INYOKA_MODULE']
    # the path to the Inyoka instance folder
    os.environ.setdefault('INYOKA_INSTANCE', realpath(join(conts, pardir)))

    #: bind the context
    ctx = ApplicationContext()
    ctx.bind()

    # setup components
    # TODO: make it configurable
    ctx.load_packages([
        'inyoka.core.*',
        'inyoka.admin.*',
        'inyoka.portal.*',
        'inyoka.news.*',
        'inyoka.forum.*',
        'inyoka.paste.*',
        'inyoka.wiki.*',
    ])

    # setup model property providers
    from inyoka.core.database import (IModelPropertyProvider, DeclarativeMeta,
                                      ModelPropertyProviderGoesWild)

    property_providers = ctx.get_implementations(IModelPropertyProvider)
    extendable_models = [m for m in DeclarativeMeta._models
                         if getattr(m, '__extendable__', False)]

    for provider in property_providers:
        try:
            model = provider.model
            extendable_models.index(model)

        except ValueError:
            raise RuntimeError('%r tries to extend a not extendable model'
                                % provider)

        else:
            for key, value in provider.properties.iteritems():
                if key not in model.__dict__:
                    setattr(model, key, value)
                else:
                    raise ModelPropertyProviderGoesWild(
                        u'%r tried to overwrite already existing '
                        u'properties (%s) on %r, aborting'
                            % (provider, key, model))


_bootstrap()
del _bootstrap
