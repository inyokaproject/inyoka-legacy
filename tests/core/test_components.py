# -*- coding: utf-8 -*-
"""
    test_components
    ~~~~~~~~~~~~~~~

    Tests for our component system

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from nose.tools import *
from inyoka import Component, ComponentMeta, setup_components


# cleanup metadata registry before testing 'cause it's possible that
# there are already registered components
ComponentMeta._registry = {}


class ComponentType(Component):
    pass


class ComponentType2(Component):
    pass


class Implementation(ComponentType):
    pass


class Implementation2(ComponentType, ComponentType2):
    pass


def test_components():
    assert_true(ComponentType._iscomptype)
    assert_true(Implementation._iscomptype)
    eq_(Implementation._comptypes, [ComponentType])
    eq_(Implementation2._comptypes, [ComponentType, ComponentType2])

    # we return the component object unchanged so it does not
    # have any special attributes
    obj = Component()
    assert_false(hasattr(obj, '_iscomptype'))
    assert_false(hasattr(obj, '_comptypes'))


def test_setup_components():
    map = setup_components(['tests.core.test_components.*'])
    eq_(len(map), 2)
    assert_true(isinstance(map[Implementation], Implementation))
    assert_true(isinstance(map[Implementation2], Implementation2))
    assert_false(ComponentType in map)
    assert_false(ComponentType2 in map)
    eq_(len(ComponentType.get_component_classes()), 2)
    eq_(len(ComponentType2.get_component_classes()), 1)
