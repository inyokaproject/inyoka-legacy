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


INYOKA_REVISION = 'unknown'


class ComponentMeta(type):
    """Metaclass that keeps track of all derived component implementations."""

    _registry = {}

    def __new__(mcs, classname, bases, dict_):
        obj = type.__new__(mcs, classname, bases, dict_)
        if bases == (object,):
            # `Component` itself
            return obj

        if Component in bases:
            # A component type
            module = dict_['__module__']
            obj._iscomptype = True
            uniquename = module + '.' + classname
            if uniquename in ComponentMeta._registry:
                raise RuntimeError(u'Component type with name %r already '
                                   u'exists' % uniquename)
            ComponentMeta._registry[uniquename] = True
        else:
            # A component
            obj._comptypes = comptypes = []
            obj._iscomptype = False
            for base in bases:
                if '_iscomptype' in base.__dict__:
                    comptypes.append(base)
                elif '_comptypes' in base.__dict__:
                    comptypes.extend(base._comptypes)
        return obj


class Component(object):
    """Base component class.

    A component is some kind of functionality provider that needs to
    be subclassed to implement the real features.

    That way a :class:`Component` can keep track of all subclasses and
    thanks to that knows all implemented “features” for that kind of component.

    """
    __metaclass__ = ComponentMeta

    def __init__(self, ctx=None):
        self.ctx = ctx


def _is_component(value):
    _registry = ComponentMeta._registry
    return (isclass(value) and issubclass(value, Component) and
            not value is Component)


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
    """"""

    def __init__(self):
        #: Component type -> classes mapping
        self._components = {}
        #: Component class -> instance mapping
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
        from inyoka.core.context import local
        local.ctx = self
        local.config = self.cfg

    @cached_property
    def application(self):
        from inyoka.application import make_app
        return make_app(self)

    def load_component(self, component):
        try:
            for comptype in component._comptypes:
                self._components.setdefault(comptype, []).append(component)
        except (AttributeError, TypeError):
            # fail silently if we try to register an interface but raise
            # if there's something compleatly wrong
            if not hasattr(component, '_iscomptype'):
                raise RuntimeError(u'Type %r is not a component' % component)
        else:
            return component

    def load_components(self, components):
        ret = []
        for component in components:
            loaded = self.load_component(component)
            if loaded:
                ret.append(loaded)
        return ret

    def unload_components(self, components):
        unloaded = []
        for component in components:
            try:
                if getattr(component, '_iscomptype', False):
                    unloaded.append(self._components.pop(component))
            except:
                # fail silently if component is not loaded
                continue

    def load_packages(self, packages):
        modules = _import_modules(packages)
        components = list(m[1] for m in
            sum((getmembers(mod, _is_component) for mod in modules), [])
        )
        return self.load_components(components)

    def get_component_classes(self, comptype):
        return self._components.get(comptype, ())

    def get_component_instances(self, comptype):
        instances = []
        for cls in self.get_component_classes(comptype):
            instances.append(self.get_component(cls))
        return instances

    def get_component(self, compcls):
        """Return the instance of a component class."""
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
            'tests.core.test_subscriptions.*',
        ]

    # TODO: make it configurable
    ctx.load_packages([
        'inyoka.testing.*',
        'inyoka.core.*',
        'inyoka.portal.*',
        'inyoka.news.*',
        'inyoka.forum.*',
        'inyoka.paste.*',
    ] + test_components)

    # setup model property extenders
    from inyoka.core.database import (IModelPropertyExtender, DeclarativeMeta,
                                      ModelPropertyExtenderGoesWild)

    property_extenders = ctx.get_component_classes(IModelPropertyExtender)
    extendable_models = [m for m in DeclarativeMeta._models
                         if getattr(m, '__extendable__', False)]
    for model in extendable_models:
        for extender in property_extenders:
            if extender.model is not model:
                continue

            for key, value in extender.properties.iteritems():
                if key not in model.__dict__:
                    setattr(model, key, value)
                else:
                    raise ModelPropertyExtenderGoesWild(
                        u'%r tried to overwrite already existing '
                        u'properties on %r, aborting'
                            % (extender, model))

_bootstrap()
del _bootstrap
