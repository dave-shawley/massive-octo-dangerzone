from unittest import mock
import unittest

from familytree import storage
from .. import ActArrangeAssertTestCase, PatchingMixin


class WhenBaseUrlMixinRequests(PatchingMixin, ActArrangeAssertTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()

        cls.mixin = storage.BaseUrlMixin(base_url='http://example.com/path')

        # after BaseUrlMixin.__init__ to avoid super() call in __init__
        super_lookup = cls.create_patch(
            'familytree.storage.super', create=True)
        cls.super_request = super_lookup.return_value.request

    @classmethod
    def action(cls):
        pass

    def setup(self):
        self.super_request.reset_mock()

    def should_concatenate_relative_path(self):
        self.mixin.request(mock.sentinel.method, 'relative/url')
        self.super_request.assert_called_once_with(
            mock.sentinel.method, 'http://example.com/path/relative/url')
