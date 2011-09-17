"""
Tests for the analytical.utils module.
"""

import re

from django.http import HttpRequest
from django.template import Context
from django.conf import settings

from analytical.utils import (
    is_internal_ip, get_required_setting,
    AnalyticalMissingSetting, AnalyticalIncorrectFormat)
from analytical.tests.utils import (
    TestCase, override_settings, SETTING_DELETED)


class SettingDeletedTestCase(TestCase):
    @override_settings(USER_ID=SETTING_DELETED)
    def test_deleted_setting_raises_exception(self):
        self.assertRaises(AttributeError, getattr, settings, "USER_ID")

    @override_settings(USER_ID=1)
    def test_only_disable_within_context_manager(self):
        """
        Make sure deleted settings returns once the block exits.
        """
        self.assertEqual(settings.USER_ID, 1)

        with override_settings(USER_ID=SETTING_DELETED):
            self.assertRaises(AttributeError, getattr, settings, "USER_ID")

        self.assertEqual(settings.USER_ID, 1)

    def test_get_required_setting(self):
        """
        Make sure using get_required_setting fails with the right
        exception.
        """
        with override_settings(USER_ID=SETTING_DELETED):
            self.assertRaises(AnalyticalMissingSetting,
                              get_required_setting, "USER_ID", re.compile("\d+"), "invalid USER_ID")

        with override_settings(USER_ID="abc"):
            self.assertRaises(AnalyticalIncorrectFormat,
                              get_required_setting, "USER_ID", re.compile("\d+"), "invalid USER_ID")

class InternalIpTestCase(TestCase):

    @override_settings(ANALYTICAL_INTERNAL_IPS=['1.1.1.1'])
    def test_render_no_internal_ip(self):
        context = Context()
        self.assertFalse(is_internal_ip(context))

    @override_settings(ANALYTICAL_INTERNAL_IPS=['1.1.1.1'])
    def test_render_internal_ip(self):
        req = HttpRequest()
        req.META['REMOTE_ADDR'] = '1.1.1.1'
        context = Context({'request': req})
        self.assertTrue(is_internal_ip(context))

    @override_settings(TEST_INTERNAL_IPS=['1.1.1.1'])
    def test_render_prefix_internal_ip(self):
        req = HttpRequest()
        req.META['REMOTE_ADDR'] = '1.1.1.1'
        context = Context({'request': req})
        self.assertTrue(is_internal_ip(context, 'TEST'))

    @override_settings(INTERNAL_IPS=['1.1.1.1'])
    def test_render_internal_ip_fallback(self):
        req = HttpRequest()
        req.META['REMOTE_ADDR'] = '1.1.1.1'
        context = Context({'request': req})
        self.assertTrue(is_internal_ip(context))

    @override_settings(ANALYTICAL_INTERNAL_IPS=['1.1.1.1'])
    def test_render_internal_ip_forwarded_for(self):
        req = HttpRequest()
        req.META['HTTP_X_FORWARDED_FOR'] = '1.1.1.1'
        context = Context({'request': req})
        self.assertTrue(is_internal_ip(context))

    @override_settings(ANALYTICAL_INTERNAL_IPS=['1.1.1.1'])
    def test_render_different_internal_ip(self):
        req = HttpRequest()
        req.META['REMOTE_ADDR'] = '2.2.2.2'
        context = Context({'request': req})
        self.assertFalse(is_internal_ip(context))
