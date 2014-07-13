import requests

from familytree import storage

from .. import ActArrangeAssertTestCase


class WhenCreatingObject(ActArrangeAssertTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls._nodes_to_remove = []
        cls.data = {'name': 'some name'}
        cls.storage = storage.StorageLayer()
        cls.storage._session.hooks['response'].append(
            cls._process_neo_response)

    @classmethod
    def action(cls):
        cls.object = cls.storage.create_object('Person', cls.data)

    @classmethod
    def annihilate(cls):
        super().annihilate()
        while cls._nodes_to_remove:
            requests.delete(cls._nodes_to_remove.pop())

    @classmethod
    def _process_neo_response(cls, response, **kwargs):
        if (response.ok and response.text and
                response.request.method in ('POST', 'PUT')):
            body = response.json()
            if body.get('self'):
                cls._nodes_to_remove.append(body['self'])
        return response

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
