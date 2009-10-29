# -*- coding: utf-8 -*-
"""
    inyoka
    ~~~~~~

    The inyoka portal system.  The system is devided into multiple modules
    to which we refer as applications.  The name inyoka means "snake" in
    zulu and was chosen because it's a python application *cough*.

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
            for base in bases:
                if issubclass(base, Component):
                    comptypes.append(base)

            for comp in comptypes:
                ComponentMeta._registry.setdefault(comp, []).append(obj)

        return obj


class Component(object):
    """Base component class.

    A component is some kind of functionality provider that needs to
    be subclassed to implement the real features.  That way a :cls:`Component`
    can keep track of all subclasses and thanks to that knows all
    implemented “features” for that kind of component.

    A simple example:

    .. sourcecode: python

        >>> class AttachmentProvider(Component):
        ...     def get_id(self):
        ...         raise NotImplementedError()
        ...
        >>> class NonBoundAttachmentProvider(AttachmentProvider):
        ...     def get_id(self):
        ...         return 'non_bound'
        ...
        >>> class ForumPostAttachmentProvider(AttachmentProvider):
        ...     def get_id(self):
        ...         return 'forum_post'
        ...
        >>> AttachmentProvider.get_component_classes()
        []

    :meth:`get_component_classes` would return `ForumPostAttachmentProvider` and
    `NonBoundAttachmentProvider` if they were activated (That's not the case,
    in this example, so it returns []).
    """
    __metaclass__ = ComponentMeta

    _implementations = []
    _instances = []

    @classmethod
    def get_components(cls):
        """return a list of all component instances for this class"""
        return cls._instances

    @classmethod
    def get_component_classes(cls):
        """returns a list of all component classes for this class"""
        return cls._implementations


def component_is_activated(imp, accepted_components):
    """This method is used to determine whether a component should get
    activated or not.
    """
    return True # Allow every implementation for now
#    return ("%s.%s" % (imp.__module__, imp.__name__) in accepted_components or
#            "%s.*" % imp.__module__ in accepted_components)


def setup_components(accepted_components):
    """Set up the :cls:`Component`'s implementation and instance lists.
    Should get called early during application setup, cause otherwise the
    components won't return any implementations.

    :param accepted_components: Modules to import to setupt the components.
    :return: An instance map containing all registered and activated components
    :return type: dict
    """
    from werkzeug import import_string
    # Import the components to setup the metaclass magic.
    for comp in accepted_components:
        import_string(comp if comp[-1] != '*' else comp[:-2])

    instance_map = {}
    for comp, implementations in ComponentMeta._registry.items():
        # Only add those components to the implementation list,
        # which are activated
        comp._implementations = [imp for imp in implementations if
                                 component_is_activated(imp, accepted_components)]
        for i in comp._implementations:
            if i not in instance_map:
                #TODO: pass something like a context object so that
                #      components don't have to query the thread-local
                #      too much? --entequak
                instance_map[i] = i()

        comp._instances = [instance_map[i] for i in comp._implementations]
    return instance_map


def _bootstrap():
    """Get the inyoka version and store it."""
    global INYOKA_REVISION
    import os
    from subprocess import Popen, PIPE

    # get inyoka revision
    hg = Popen(['hg', 'tip'], stdout=PIPE, stderr=PIPE, stdin=PIPE,
               cwd=os.path.dirname(__file__))
    hg.stdin.close()
    hg.stderr.close()
    rv = hg.stdout.read()
    hg.stdout.close()
    hg.wait()
    hg_node = None
    if hg.wait() == 0:
        for line in rv.splitlines():
            p = line.split(':', 1)
            if len(p) == 2 and p[0].lower().strip() == 'changeset':
                hg_node = p[1].strip()
                break
    INYOKA_REVISION = hg_node


_bootstrap()
del _bootstrap
