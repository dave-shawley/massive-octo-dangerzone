from unittest import mock

from requests import exceptions

from familytree import storage
from .. import ActArrangeAssertTestCase, PatchingMixin, RandomValueMixin


########################################################################
# NeoSession.__init__
########################################################################

class WhenCreatingNeoSession(ActArrangeAssertTestCase):

    @classmethod
    def action(cls):
        cls.session = storage.NeoSession()

    def should_set_base_url(self):
        assert self.session.base_url == 'http://localhost:7474/db/data/'


########################################################################
# NeoSession.action_links
########################################################################

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


########################################################################
# NeoSession.request
########################################################################

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


########################################################################
# NeoSession.ensure_indexed
########################################################################

class EnsureIndexTestCase(RandomValueMixin, ActArrangeAssertTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.object_label = cls.get_generated_string('object label')

        cls.session = storage.NeoSession()
        cls.session.get = mock.MagicMock()
        cls.session.post = mock.Mock()
        cls.session._action_links = {'indexes': 'http://index-url/'}

    @classmethod
    def action(cls):
        cls.session.ensure_indexed(cls.object_label)


class WhenEnsuringAnIndexThatDoesNotExist(EnsureIndexTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.session._indexes = mock.MagicMock(spec=set)
        cls.session._indexes.__contains__.side_effect = [False, False]

    def should_check_for_index_twice(self):
        call_list = self.session._indexes.__contains__.call_args_list
        assert call_list == [
            mock.call(self.object_label), mock.call(self.object_label)]

    def should_retrieve_indexes(self):
        self.session.get.assert_called_once_with('indexes')

    def should_check_retrieve_result(self):
        response = self.session.get.return_value
        response.raise_for_status.assert_called_once_with()

    def should_update_index_list(self):
        response = self.session.get.return_value
        self.session._indexes.clear.assert_called_once_with()
        self.session._indexes.update.assert_called_once_with(
            {info['label'] for info in response.json.return_value})

    def should_create_index(self):
        self.session.post.assert_called_once_with(
            'http://index-url/{0}'.format(self.object_label),
            data={'property_keys': ['externalId']},
        )

    def should_check_create_result(self):
        response = self.session.post.return_value
        response.raise_for_status.assert_called_once_with()

    def should_append_to_index_property(self):
        self.session._indexes.add.assert_called_once_with(self.object_label)


class WhenEnsuringAnIndexThatIsAddedExternally(EnsureIndexTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.session._indexes = mock.MagicMock(spec=set)
        cls.session._indexes.__contains__.side_effect = [False, True]

    def should_check_for_index_twice(self):
        call_list = self.session._indexes.__contains__.call_args_list
        assert call_list == [
            mock.call(self.object_label), mock.call(self.object_label)]

    def should_retrieve_indexes(self):
        self.session.get.assert_called_once_with('indexes')

    def should_check_retrieve_result(self):
        response = self.session.get.return_value
        response.raise_for_status.assert_called_once_with()

    def should_update_index_list(self):
        response = self.session.get.return_value
        self.session._indexes.clear.assert_called_once_with()
        self.session._indexes.update.assert_called_once_with(
            {info['label'] for info in response.json.return_value})

    def should_not_create_index(self):
        assert not self.session.post.called


class WhenEnsuringAnIndexThatExists(EnsureIndexTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.session._indexes.add(cls.object_label)

    def should_not_retrieve_indexes(self):
        assert not self.session.get.called

    def should_not_create_index(self):
        assert not self.session.post.called


########################################################################
# NeoSession.find_object
########################################################################

class WhenFindingObjectAndLookupFails(
        RandomValueMixin, ActArrangeAssertTestCase):

    expected_exceptions = exceptions.RequestException

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.session = storage.NeoSession()
        cls.session.get = mock.Mock()
        cls.session.get.return_value.raise_for_status.side_effect = (
            exceptions.HTTPError)

    @classmethod
    def action(cls):
        cls.obj = cls.session.find_object(
            cls.get_generated_string(), cls.get_generated_string())

    @property
    def get_response(self):
        return self.session.get.return_value

    def should_raise_for_status(self):
        self.get_response.raise_for_status.assert_called_once_with()

    def should_propagate_exception(self):
        assert isinstance(self.raised_exception, exceptions.HTTPError)
