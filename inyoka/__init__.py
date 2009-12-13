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

INYOKA_REVISION = 'unknown'


class ComponentMeta(type):
    """Metaclass that keeps track of all derived component implementations."""

    _registry = {}

    def __new__(mcs, name, bases, dict_):
        obj = type.__new__(mcs, name, bases, dict_)
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

    _implementations = ()
    _instances = ()

    def __init__(self, ctx=None):
        self.ctx = ctx

    @classmethod
    def get_components(cls):
        """Return a list of all component instances for this class."""
        return cls._instances

    @classmethod
    def get_component_classes(cls):
        """Return a list of all component classes for this class."""
        return cls._implementations


def component_is_activated(imp, accepted_components):
    """This method is used to determine whether a component should get
    activated or not.
    """
    return True # Allow every implementation for now
#    return ("%s.%s" % (imp.__module__, imp.__name__) in accepted_components or
#            "%s.*" % imp.__module__ in accepted_components)


def setup_components(accepted_components):
    """Set up the :class:`Component`'s implementation and instance lists.
    Should get called early during application setup, cause otherwise the
    components won't return any implementations.

    :param accepted_components: Modules to import to setupt the components.
    :return: An instance map containing all registered and activated components
    :rtype: dict
    """
    from werkzeug import import_string
    from inyoka.core.api import ctx
    # Import the components to setup the metaclass magic.
    for comp in accepted_components:
        import_string(comp if comp[-1] != '*' else comp[:-2])

    instance_map = {}
    for comp, implementations in ComponentMeta._registry.items():
        # Only add those components to the implementation list,
        # which are activated
        appender = []
        for imp in implementations:
            if component_is_activated(imp, accepted_components):
                appender.append(imp)
            imp._implementations = subimplements = tuple(imp.__subclasses__())
            appender.extend(subimplements)
        comp._implementations = tuple(appender[:])

        for i in comp._implementations:
            if i not in instance_map:
                instance_map[i] = i(ctx)

        comp._instances = tuple(instance_map[i] for i in comp._implementations)
    return instance_map


def _bootstrap():
    """Get the inyoka version and store it."""
    global INYOKA_REVISION
    import os
    from os.path import realpath, dirname, join, pardir, isdir
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
            p = line.split(':', 1)
            if len(p) == 2 and p[0].lower().strip() == 'changeset':
                hg_node = p[1].strip()
                break
    INYOKA_REVISION = hg_node

    # the path to the contents of the inyoka package
    os.environ['instance_folder'] = conts = realpath(join(dirname(__file__)))
    # the path to the folder where the inyoka package is stored in
    os.environ['package_folder'] = realpath(join(conts, pardir))


_bootstrap()
del _bootstrap
