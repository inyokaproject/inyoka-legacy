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

class ComponentMeta(type):
    """Metaclass that keeps track of all derived component implementations."""

    _registry = {}

    def __new__(mcs, name, bases, dict_):
        obj = type.__new__(mcs, name, bases, dict_)
        if bases == (object,):
            # `Component` itself
            return obj

        if Component in bases:
            obj._iscomptype = True
        else:
            obj._comptypes = comptypes = []
            for base in bases:
                if '_iscomptype' in base.__dict__:
                    comptypes.append(base)
                elif '_comptypes' in base.__dict__:
                    comptypes.extend(base._comptypes)

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

def _helper(imp, accepted_components):
    return ("%s.%s" % (imp.__module__, imp.__name__) in accepted_components or
            "%s.*" % imp.__module__ in accepted_components)

#def setup_components(accepted_components):
#    # todo import the components
#    for c, implementations in ComponentMeta._registry.items():
#        c._implementations = [imp for imp in implementations if _helper(imp, accepted_components)]
#        c._instances = [i() for i in c._implementations]

def _bootstrap():
    """Get the inyoka version and store it."""
    global INYOKA_REVISION
    import os, inyoka
    from subprocess import Popen, PIPE

    # get inyoka revision
    hg = Popen(['hg', 'tip'], stdout=PIPE, stderr=PIPE, stdin=PIPE,
               cwd=os.path.dirname(inyoka.__file__))
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
