# -*- coding: utf-8 -*-
"""
    test_components
    ~~~~~~~~~~~~~~~

    Tests for our component system

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka import Interface, InterfaceMeta, _is_interface, _import_modules
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

class Implementation3(Interface3):
    pass


_test_components = [Interface1, Interface2, Interface3,
                    Implementation1, Implementation2, Implementation3]


def _teardown_components():
    ctx.unload_components(_test_components)


def _setup_components():
    ctx.load_components(_test_components)


@with_setup(_setup_components, _teardown_components)
def test_component_is_activated():
    assert_false(ctx.component_is_activated(Implementation1, ['tests.core.*']))
    assert_false(ctx.component_is_activated(Implementation1,
                                ['tests.core.test_components.Implementation1']))

    assert_true(ctx.component_is_activated(Implementation2,
                                ['tests.core.test_components.Implementation1']))

    eq_(ctx.load_packages(['tests.core.test_components'], ['tests.core.*']),
                          set([]))

    eq_(ctx.load_packages(['tests.core.test_components'],
                          ['tests.core.test_components.Implementation1']),
                          set([Implementation2,Implementation3]))


@with_setup(teardown=_teardown_components)
def test_load_components():
    loaded = ctx.load_components([Implementation1, Implementation2, Implementation3])
    eq_(len(loaded), 3)

    assert_true(Implementation1 in loaded)
    assert_true(Implementation2 in loaded)
    assert_true(Implementation3 in loaded)
    assert_false(Interface1 in loaded)
    assert_false(Interface2 in loaded)
    assert_false(Interface3 in loaded)

    eq_(len(ctx.get_implementations(Interface1)), 2)
    eq_(len(ctx.get_implementations(Interface2)), 2)


@with_setup(_setup_components)
def test_unload_components():
    _comps = (Interface1, Interface2)
    ctx.unload_components(_comps)
    for comp in _comps:
        assert_false(comp in InterfaceMeta._registry)

    # test that we fail silently if a component is not loaded
    ctx.unload_components(_comps)


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


def test_import_modules():
    from inyoka.core.auth import models
    # import definite modules
    assert_true(models is list(_import_modules(('inyoka.core.auth.models',)))[0])
    # star import packages
    assert_true(models in list(_import_modules(('inyoka.core.*',))))
    # star import to definite modules not packages
    # we assert here to import the module rather than to raise a ValueError
    # as werkzeug's find_modules would do.
    list(_import_modules(('werkzeug._internal.*',)))


def test_automatical_config_creation():
    import os
    from inyoka import ApplicationContext
    from inyoka.core.api import ctx
    from inyoka.core.config import Configuration
    # ensure that our config file really exists
    assert_true(ctx.cfg.exists)
    # remove the config file and ensure that it's really removed
    # and marked as such by our configuration system.
    fn = ctx.cfg.filename
    content = open(fn).read()
    os.remove(fn)
    assert_false(Configuration(fn).exists)
    # check that it's created automatically by our :cls:`ApplicationContext`
    new_ctx = ApplicationContext()
    assert_true(os.path.exists(fn))
    open(fn, 'w').write(content)
