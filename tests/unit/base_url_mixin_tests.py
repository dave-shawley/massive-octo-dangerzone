from unittest import mock

from familytree import storage
from .. import ActArrangeAssertTestCase, PatchingMixin


class WhenCreatingBaseUrlMixin:

    def should_append_trailing_slash_when_necessary(self):
        mixin = storage.BaseUrlMixin('http://no-trailing-slash')
        assert mixin.base_url == 'http://no-trailing-slash/'

    def should_not_append_slash_when_already_there(self):
        mixin = storage.BaseUrlMixin('http://trailing-slash/')
        assert mixin.base_url == 'http://trailing-slash/'


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
