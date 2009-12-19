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
from functools import partial

INYOKA_REVISION = 'unknown'


class ComponentMeta(type):
    """Metaclass that keeps track of all derived component implementations."""

    _registry = {}

    def __new__(mcs, classname, bases, dict_):
        obj = type.__new__(mcs, classname, bases, dict_)
        if bases == (object,):
            # `Component` itself
            return obj

        if Component not in bases:
            obj._comptypes = comptypes = []
            obj._iscomptype = False
            for base in bases:
                if issubclass(base, Component):
                    comptypes.append(base)

            for comp in comptypes:
                ComponentMeta._registry.setdefault(comp, []).append(obj)
        else:
            obj._iscomptype = True

        return obj


class Component(object):
    """Base component class.

    A component is some kind of functionality provider that needs to
    be subclassed to implement the real features.

    That way a :class:`Component` can keep track of all subclasses and
    thanks to that knows all implemented “features” for that kind of component.

    """
    __metaclass__ = ComponentMeta

    #: If `True` a component will be lazy loaded (instanciated) on first
    #: access.  If `False` (default) it will be instanciated immediatly
    #: till imported.
    __lazy_loading__ = False

    _implementations = ()
    _instances = ()

    def __init__(self, ctx=None):
        self.ctx = ctx

    @classmethod
    def get_components(cls):
        """Return a list of all component instances for this class."""
        def _init():
            for impl in cls._instances:
                yield impl()
        # setup lazy loading components and disable loading after that process
        # so that we don't load them twice
        if cls.__lazy_loading__:
            cls._instances = tuple(_init())
            cls.__lazy_loading__ = False
        return cls._instances

    @classmethod
    def get_component_classes(cls):
        """Return a list of all component classes for this class."""
        return cls._implementations


def component_is_activated(imp, accepted_modules):
    """This method is used to determine whether a component should get
    activated or not.
    """
    # TODO: only do the splitting once…
    modules = [i.strip('.*') for i in accepted_modules]
    cname = imp.__module__ + '.' + imp.__name__
    while cname:
        if cname in modules:
            return True
        idx = cname.rfind('.')
        if idx < 0:
            break
        cname = cname[:idx]

    return False


def setup_components(accepted_modules):
    """Set up the :class:`Component`'s implementation and instance lists.
    Should get called early during application setup, cause otherwise the
    components won't return any implementations.

    :param accepted_modules: Modules to import to setupt the components.
                                Can be an empty list to setup only known components.
    :return: An instance map containing all registered and activated components
    :rtype: dict
    """
    from werkzeug import import_string, find_modules
    from inyoka.core.api import ctx
    # Import the components to setup the metaclass magic.
    for module in accepted_modules:
        # No star at the end means a package/module/class but nothing below.
        if module[-1] != '*':
            import_string(module[:-2])
        else:
            try:
                for mod in find_modules(module[:-2], recursive=True):
                    import_string(mod)
            except ValueError: # module is a module and not a package
                import_string(module[:-2])

    instance_map = {}
    for comp, implementations in ComponentMeta._registry.items():
        # Only add those components to the implementation list,
        # which are activated
        appender = []
        for imp in implementations:
            if component_is_activated(imp, accepted_modules):
                appender.append(imp)
            imp._implementations = subimplements = tuple(imp.__subclasses__())
            appender.extend(subimplements)
        comp._implementations = tuple(appender[:])

        for impl in comp._implementations:
            if impl not in instance_map:
                if impl.__lazy_loading__:
                    instance = partial(impl, ctx)
                else:
                    instance = impl(ctx)
                instance_map[impl] = instance

        comp._instances = tuple(instance_map[i] for i in comp._implementations)
    return instance_map


def _bootstrap():
    """Get the inyoka version and store it."""
    global INYOKA_REVISION
    import os
    from os.path import realpath, dirname, join, pardir
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

    # setup config
    from inyoka.core.context import local
    from inyoka.core.config import Configuration, config
    cfile = os.environ.get('INYOKA_CONFIG', 'inyoka.ini')
    local.config = config = Configuration(
        join(realpath(os.environ['INYOKA_INSTANCE']), cfile))

    if not config.exists:
        trans = config.edit()
        trans.commit(force=True)
        config.touch()

    # setup components
    test_components = []
    if config['debug']:
        test_components = [
            'tests.core.test_subscriptions.*',
        ]

    # TODO: make it configurable
    setup_components([
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

    property_extenders = IModelPropertyExtender.get_component_classes()
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
