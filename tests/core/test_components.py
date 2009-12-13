# -*- coding: utf-8 -*-
"""
    test_components
    ~~~~~~~~~~~~~~~

    Tests for our component system

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka import Component, ComponentMeta, setup_components
from inyoka.core.api import ctx
from inyoka.core.test import *


# cleanup metadata registry before testing 'cause it's possible that
# there are already registered components
ComponentMeta._registry = {}


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


def test_setup_components():
    map = setup_components(['tests.core.test_components.*'])
    eq_(len(map), 4)
    assert_true(isinstance(map[Implementation1], Implementation1))
    assert_true(isinstance(map[Implementation2], Implementation2))
    assert_false(Interface in map)
    assert_false(Interface2 in map)
    eq_(len(Interface.get_component_classes()), 4)
    eq_(len(Interface2.get_component_classes()), 1)
