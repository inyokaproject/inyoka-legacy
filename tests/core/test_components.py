# -*- coding: utf-8 -*-
"""
    test_components
    ~~~~~~~~~~~~~~~

    Tests for our component system

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka import Component, ComponentMeta, setup_components, \
    teardown_components, component_is_activated, _assert_one_type

from inyoka.core.api import ctx
from inyoka.core.test import *


class Interface(Component):
    pass

class Interface2(Component):
    pass

class InterfaceDescription(Interface):
    pass

class Implementation1(Interface):
    pass

class Implementation2(InterfaceDescription):
    pass

class Implementation3(Interface, Interface2):
    pass


_components = [Interface, Interface2, InterfaceDescription, Implementation1,
               Implementation2, Implementation3]

def _teardown_components():
    teardown_components(_components)


def _setup_components():
    setup_components(_components)


@future
def test_component_is_activated():
    _activated, comp_type = [Implementation1, Implementation2], type(Component)

    assert_true(component_is_activated(Implementation1, _activated, comp_type))
    assert_false(component_is_activated(Implementation3, _activated, comp_type))

    _activated = ['tests.core.test_components.*', 'tests.foo.bar.*']
    assert_true(component_is_activated(Implementation1, _activated, str))
    assert_true(component_is_activated(Implementation3, _activated, str))


def test_assert_one_type():
    assert_true(_assert_one_type(['foo', 'bar', 'baz']))
    # all those are component types and as such supported
    assert_true(_assert_one_type([Implementation1, Implementation2, Interface]))
    # we only support component and string types
    assert_raises(AssertionError, _assert_one_type, ['str', 1, 'foo'])
    assert_raises(AssertionError, _assert_one_type, [1, 3, 3, 4])


def test_setup_components():
    map = setup_components([Implementation1, Implementation2, Implementation3])
    eq_(len(map), 3)

    implementations = [Implementation1, Implementation2, Implementation3]

    keys = map.keys()
    for idx in xrange(3):
        assert_true(keys.pop() in implementations)

    eq_(keys, [])

    assert_true(isinstance(map[Implementation1], Implementation1))
    assert_true(isinstance(map[Implementation2], Implementation2))
    assert_false(Interface in map)
    assert_false(Interface2 in map)

    eq_(len(Interface.get_component_classes()), 3)
    eq_(len(Interface2.get_component_classes()), 1)

    teardown_components([Implementation1, Implementation2, Implementation3])


@with_setup(_setup_components)
def test_teardown_components():
    _comps = (Interface, Interface2, InterfaceDescription)
    teardown_components(_comps)
    for comp in _comps:
        assert_false(comp in ComponentMeta._registry)


def test_components():
    assert_true(Interface._iscomptype)
    assert_false(InterfaceDescription._iscomptype)
    assert_false(Implementation1._iscomptype)
    eq_(Implementation1._comptypes, [Interface])
    eq_(Implementation2._comptypes, [InterfaceDescription])
    eq_(Implementation3._comptypes, [Interface, Interface2])

    # we return the component object unchanged so it does not
    # have any special attributes
    obj = Component(ctx)
    assert_false(hasattr(obj, '_iscomptype'))
    assert_false(hasattr(obj, '_comptypes'))
