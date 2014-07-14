import uuid

import requests

from familytree import storage
from . import NeoTestingMixin
from .. import ActArrangeAssertTestCase


class WhenCreatingObject(NeoTestingMixin, ActArrangeAssertTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.data = {'name': 'some name'}
        cls.storage = storage.StorageLayer()
        cls.monitor_session(cls.storage._session)

    @classmethod
    def action(cls):
        cls.object = cls.storage.create_object('Person', cls.data)

    def should_create_object_in_neo(self):
        response = requests.get(self.object.self)
        assert response.json()['data']['name'] == 'some name'

    def should_create_deterministic_external_id(self):
        assert self.object['externalId'] == storage.generate_hash(
            'Person', self.data)

    def should_label_object_by_external_id(self):
        response = requests.get(
            'http://localhost:7474/db/data/label/Person/nodes',
            params={'externalId': '"{0}"'.format(self.object['externalId'])},
            headers={'Accept': 'application/json'},
        )
        matches = response.json()
        assert len(matches) == 1
        assert matches[0] == requests.get(self.object.self).json()


class WhenNeoSessionEnsuresAnIndex(NeoTestingMixin, ActArrangeAssertTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.object_label = uuid.uuid4().hex
        cls.session = storage.NeoSession()
        cls.monitor_session(cls.session)

    @classmethod
    def action(cls):
        cls.session.ensure_indexed(cls.object_label)

    def should_ensure_index_exists(self):
        for index_info in self.neo_get('indexes'):
            if index_info['label'] == self.object_label:
                assert index_info['property_keys'] == ['externalId']
                break
        else:  # pragma nocover
            assert False, '{0} not found'.format(self.object_label)
