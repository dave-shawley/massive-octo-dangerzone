from unittest import mock

from familytree import storage
from .. import ActArrangeAssertTestCase, PatchingMixin


class WhenCreatingNeoSession(ActArrangeAssertTestCase):

    @classmethod
    def action(cls):
        cls.session = storage.NeoSession()

    def should_set_base_url(self):
        assert self.session.base_url == 'http://localhost:7474/db/data/'


class WhenReadingActionLinks(ActArrangeAssertTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.session = storage.NeoSession()
        cls.session.get = mock.Mock()
        response = cls.session.get.return_value
        response.json.return_value = {
            'trailing_slash': 'http://localhost:7474/db/data/',
            'slash_omitted': 'http://localhost:7474/db/data/index',
        }

    @classmethod
    def action(cls):
        cls.links = cls.session.action_links

    def should_retrieve_service_root(self):
        self.session.get.assert_called_once_with('', _ignore_actions=True)

    def should_deserialize_response(self):
        self.session.get.return_value.json.assert_called_once_with()

    def should_append_trailing_slash_when_needed(self):
        assert self.links['slash_omitted'].endswith('/')

    def should_not_append_slash_when_present(self):
        assert not self.links['trailing_slash'].endswith('//')


class WhenReadingActionLinksTwice(WhenReadingActionLinks):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.first_links = cls.session.action_links

    def should_return_same_instance_both_times(self):
        assert self.links is self.first_links


class WhenSubmittingRequestWithActionName(
        PatchingMixin, ActArrangeAssertTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        super_lookup = cls.create_patch(
            'familytree.storage.super', create=True)
        cls.base_class = super_lookup.return_value
        cls.session = storage.NeoSession()
        cls.session._action_links = {
            mock.sentinel.action: mock.sentinel.endpoint,
        }

    @classmethod
    def action(cls):
        cls.response = cls.session.request(
            mock.sentinel.method, mock.sentinel.action)

    def should_use_endpoint_url(self):
        self.base_class.request.assert_called_once_with(
            mock.sentinel.method, mock.sentinel.endpoint)


class WhenSubmittingRequestWithNonAction(
        PatchingMixin, ActArrangeAssertTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        super_lookup = cls.create_patch(
            'familytree.storage.super', create=True)
        cls.base_class = super_lookup.return_value
        cls.session = storage.NeoSession()
        cls.session._action_links = {}

    @classmethod
    def action(cls):
        cls.response = cls.session.request(
            mock.sentinel.method, mock.sentinel.url)

    def should_pass_url_to_base_class(self):
        self.base_class.request.assert_called_once_with(
            mock.sentinel.method, mock.sentinel.url)
