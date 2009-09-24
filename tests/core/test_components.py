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

class Subcomponent(ComponentType):
    pass

class Implementation(ComponentType):
    pass

class Implementation2(ComponentType, ComponentType2):
    pass

class Implementation3(Subcomponent):
    pass


def test_components():
    assert_true(ComponentType._iscomptype)
    assert_true(Implementation._iscomptype)

    eq_(Implementation._comptypes, [ComponentType])
    eq_(Implementation2._comptypes, [ComponentType, ComponentType2])
    #XXX: here we go with a second fancy thing... Why is `ComponentType`
    #     twice in the list?
    eq_(Implementation3._comptypes, [ComponentType, Subcomponent])


def test_setup_components():
    map = setup_components(['tests.core.test_components.*'])
    print map, len(map)
    eq_(len(map), 4)
    assert_true(isinstance(map[Implementation], Implementation))
    assert_true(isinstance(map[Implementation2], Implementation2))
    assert_true(isinstance(map[Implementation3], Implementation3))
    assert_false(ComponentType in map)
    eq_(len(ComponentType._implementations), 4)
    eq_(len(ComponentType2._implementations), 1)
    #XXX: why in gods name does this return `4` not `1`?
    eq_(len(Subcomponent._implementations), 1)
