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
