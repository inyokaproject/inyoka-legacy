# -*- coding: utf-8 -*-
"""
    test_components
    ~~~~~~~~~~~~~~~

    Tests for our component system

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka import Interface, InterfaceMeta
from inyoka.core.api import ctx
from inyoka.core.test import *


class Interface1(Interface):
    pass

class Interface2(Interface):
    pass

class Interface3(Interface2, Interface):
    pass

class Implementation1(Interface1):
    pass

class Implementation2(Interface1, Interface2):
    pass

class Implementation3(Interface2, Interface):
    pass

class Implementation4(Interface3):
    pass


_test_components = [Interface1, Interface2, Interface3,
                    Implementation1, Implementation2, Implementation3,
                    Implementation4]


def _teardown_components():
    ctx.load_components(_test_components)


def _setup_components():
    ctx.unload_components(_test_components)


@future
def test_component_is_activated():
    #TODO: components are for now alway activated if loaded.  We need to implement
    #      that feature again.
    _activated = set([Implementation1, Implementation2])

    assert_true(component_is_activated(Implementation1, _activated))
    assert_false(component_is_activated(Implementation3, _activated))

    _activated = ['tests.core.test_components.*', 'tests.foo.bar.*']
    assert_true(component_is_activated(Implementation1, _activated))
    assert_true(component_is_activated(Implementation3, _activated))


@with_setup(_teardown_components, _setup_components)
def test_load_components():
    loaded = ctx.load_components(set([Implementation1, Implementation2, Implementation4]))
    eq_(len(loaded), 3)

    assert_true(Implementation1 in loaded)
    assert_true(Implementation2 in loaded)
    assert_true(Implementation4 in loaded)
    assert_false(Interface1 in loaded)
    assert_false(Interface2 in loaded)
    assert_false(Interface3 in loaded)

    eq_(len(ctx.get_implementations(Interface1)), 2)
    eq_(len(ctx.get_implementations(Interface2)), 2)


@with_setup(teardown=_setup_components)
def test_unload_components():
    _comps = (Interface1, Interface2)
    ctx.unload_components(_comps)
    for comp in _comps:
        assert_false(comp in InterfaceMeta._registry)


def test_components():
    assert_true(Interface1._isinterface)
    assert_false(hasattr(Interface1, '_interfaces'))
    assert_false(Implementation1._isinterface)
    eq_(Implementation1._interfaces, set([Interface1]))
    eq_(Implementation2._interfaces, set([Interface1, Interface2]))

    # we return the component object unchanged so it does not
    # have any special attributes
    obj = Interface(ctx)
    assert_false(hasattr(obj, '_isinterface'))
    assert_false(hasattr(obj, '_interfaces'))


@raises(RuntimeError)
def test_double_interfaces_runtimeerror():
    class SomeInterface(Interface):
        pass

    class SomeInterface(Interface):
        pass


@raises(RuntimeError)
def test_unable_to_load_non_interface():
    class SomeDummy(object):
        pass

    ctx.load_component(SomeDummy)
