#-*- coding: utf-8 -*-
"""
    portal/test_portal_views
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module tests the portal views
"""
from inyoka.utils.test import view, ViewTestCase


@view('/', component='portal')
def test_index(resp, tctx, ctx):
    #TODO: this is just for demonstration. We need to write some
    #      more useful tests :-)
    assert tctx['pm_count'] == 0


class TestIndexView(ViewTestCase):
    #TODO: This is just for demonstration. We need to write some
    #      more useful tests :-)

    component = 'portal'

    def setup(self):
        pass

    def test_pm_count(self):
        tctx = self.get_context('/')
        assert tctx['pm_count'] == 0
