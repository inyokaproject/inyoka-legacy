# -*- coding: utf-8 -*-
"""
    test_http
    ~~~~~~~~~

    Our tests for the :mod:`inyoka.core.http` module.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.test import *
from inyoka.core.http import FlashMessage


class TestRequest(ViewTestCase):

    def test_flash_messages(self):
        with self.get_new_request() as c:
            req = c.request
            req.flash(u'Message1', False, 1)
            eq_(req.flash_messages, [FlashMessage(u'Message1', False, 1, False)])
            # we automatically clear the flash messages buffer by
            # accessing the `messages` property.
            eq_(req.flash_messages, [])
            req.flash(u'Message2', False, 2)
            req.flash(u'Message3', True, 3)
            req.flash(u'Message4', id=4)
            req.unflash(3)
            self.assertEqual(req.flash_messages, [FlashMessage(u'Message2', False, 2, False),
                FlashMessage(u'Message4', None, 4, False)])
            # test automatic id generation
            id = req.flash(u'Message5')
            assert_false(id is None)
            assert_true(isinstance(id, unicode))
