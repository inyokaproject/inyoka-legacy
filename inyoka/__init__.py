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

    _name2mod = {}

    def __new__(mcs, name, bases, dict_):
        obj = type.__new__(mcs, name, bases, dict_)
        if bases == (object,):
            # `Component` itself
            return obj
        if Component in bases:
            obj._iscomptype = True
            uniquename = dict_['__module__'] + '.' + name
            if name in ComponentMeta._name2mod:
                raise TypeError('Component type with name %r already exists' %
                                uniquename)
            ComponentMeta._name2mod[uniquename] = {}
        else:
            # A component
            obj._comptypes = comptypes = []
            for base in bases:
                basename = base.__module__ + '.' + base.__name__
                objname = obj.__module__ + '.' + obj.__name__
                ComponentMeta._name2mod[basename].update({objname: obj})
                if '_iscomptype' in base.__dict__:
                    comptypes.append(base)
                elif '_comptypes' in base.__dict__:
                    comptypes.extend(base._comptypes)
        return obj


class Component(object):
    """Base component class.

    A component is some kind of functionality provider that needs to
    be subclassed to implement the real features.  That way a :cls:`Component`
    can keep track of all subclasses and thanks to that knows all
    implemented “features” for that kind of component.

    A simple example:

    .. sourcecode: pycon

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
        >>> AttachmentProvider.get_components()
        [<class '__main__.ForumPostAttachmentProvider'>, <class '__main__.NonBoundAttachmentProvider'>]

    As you see :meth:`get_components` returns all implemented features
    for that specific component.

    """
    __metaclass__ = ComponentMeta

    @classmethod
    def get_components(cls):
        """return a list of all components from the class"""
        if hasattr(cls, '__metaclass__'):
            mcls = cls.__metaclass__
            dict_ = mcls._name2mod
            name = cls.__module__ + '.' + cls.__name__
            components = []
            for ccls in dict_.get(name, {}).itervalues():
                components.append(ccls)
            return components


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
