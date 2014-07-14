from unittest import mock

from requests import exceptions

from familytree import storage
from .. import ActArrangeAssertTestCase, RandomValueMixin


class CreateObjectTestCase(RandomValueMixin, ActArrangeAssertTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.storage_layer = storage.StorageLayer()
        cls.storage_layer._session = mock.Mock()
        cls.object_data = {
            cls.get_generated_string(): cls.get_generated_string(),
        }

        cls.create_response = mock.Mock()
        cls.create_response.json.return_value = {
            'labels': mock.sentinel.label_link,
            'data': cls.object_data.copy(),
        }

        cls.label_response = mock.Mock()

        cls.storage_layer._session.get.return_value.json.return_value = []

        cls.storage_layer._session.post.side_effect = [
            cls.create_response, cls.label_response]

    @classmethod
    def action(cls):
        cls.obj = cls.storage_layer.create_object(
            cls.get_generated_string('label'), cls.object_data)

    def _get_request_kwargs(self, url):
        for args, kwargs in self.storage_layer._session.post.call_args_list:
            if args[0] == url:
                return kwargs


class WhenCreatingObject(CreateObjectTestCase):

    @property
    def generated_object_id(self):
        return storage.generate_hash(
            self.get_generated_string('label'), self.object_data)

    def should_generate_object_id(self):
        kwargs = self._get_request_kwargs('node')
        assert kwargs['data']['externalId'] == self.generated_object_id

    def should_search_for_external_id(self):
        self.storage_layer._session.get.assert_called_once_with(
            'label/{0}/nodes'.format(self.get_generated_string('label')),
            params={'externalId': '"{0}"'.format(self.generated_object_id)},
        )

    def should_assign_object_label(self):
        kwargs = self._get_request_kwargs(mock.sentinel.label_link)
        assert kwargs['data'] == self.get_generated_string('label')

    def should_return_neo_object(self):
        assert isinstance(self.obj, storage.NeoNode)

    def should_ensure_label_is_indexed(self):
        self.storage_layer._session.ensure_indexed.assert_called_once_with(
            self.get_generated_string('label'))


class WhenCreatingObjectAndCreateRequestFails(CreateObjectTestCase):
    expected_exceptions = exceptions.RequestException

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.create_response.raise_for_status.side_effect = exceptions.HTTPError

    def should_raise_for_status(self):
        self.create_response.raise_for_status.assert_called_once_with()

    def should_propagate_exception(self):
        assert isinstance(self.raised_exception, exceptions.HTTPError)


class WhenCreatingObjectAndLabelRequestFails(CreateObjectTestCase):
    expected_exceptions = exceptions.RequestException

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.label_response.raise_for_status.side_effect = exceptions.HTTPError

    def should_raise_for_status(self):
        self.label_response.raise_for_status.assert_called_once_with()

    def should_propagate_exception(self):
        assert isinstance(self.raised_exception, exceptions.HTTPError)


class WhenCreatingObjectWithObjectId(CreateObjectTestCase):

    @classmethod
    def action(cls):
        cls.obj = cls.storage_layer.create_object(
            cls.get_generated_string('label'),
            cls.object_data,
            object_id=mock.sentinel.object_id,
        )

    def should_use_specified_object_id(self):
        kwargs = self._get_request_kwargs('node')
        assert kwargs['data']['externalId'] == mock.sentinel.object_id


class WhenCreatingObjectThatAlreadyExists(CreateObjectTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.matched_object = mock.Mock()
        cls.storage_layer._session.get.return_value.json.return_value = [
            cls.matched_object]

    def should_not_create_new_object(self):
        assert not self.storage_layer._session.post.called

    def should_return_neo_object(self):
        assert isinstance(self.obj, storage.NeoNode)


class WhenCreatingObjectAndLookupFails(CreateObjectTestCase):
    expected_exceptions = exceptions.RequestException

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.response = cls.storage_layer._session.get.return_value
        cls.response.raise_for_status.side_effect = exceptions.HTTPError

    def should_raise_for_status(self):
        self.response.raise_for_status.assert_called_once_with()

    def should_propagate_exception(self):
        assert isinstance(self.raised_exception, exceptions.HTTPError)
