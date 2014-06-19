from unittest import mock
import json
import uuid

import responses

from familytree import storage
from .. import ActArrangeAssertTestCase, PatchingMixin, TemporaryFileMixin


class RequestMixin:

    @classmethod
    def arrange(cls):
        super().arrange()
        cls._requests_session = responses.RequestsMock()
        cls._requests_session.start()

    @classmethod
    def annihilate(cls):
        super().annihilate()
        cls._requests_session.stop()

    @classmethod
    def add_json_response(cls, method, url, response):
        cls._requests_session.add(
            method, url, body=json.dumps(response).encode('utf-8'),
            content_type='application/json; charset=UTF-8')

    def _find_http_request(self, url, method):
        for call_index, call_info in enumerate(self._requests_session.calls):
            request = call_info.request
            if (request.url, request.method) == (url, method):
                return call_index, request
        return -1, None

    def assert_that_http_request_made(
            self, url, at_index=None, method='GET', body=None):

        request_index, request = self._find_http_request(url, method)
        if request_index < 0:
            raise AssertionError(
                'expected request for "{0} {1}", not found in [{2}]'.format(
                    method, url,
                    ','.join('({0}, {1})'.format(call.request.method,
                                                 call.request.url)
                             for call in self._requests_session.calls)
                )
            )
        if at_index is not None:
            if at_index != request_index:
                raise AssertionError(
                    'expected request for "{0} {1}" at index {2}, '
                    'found "{3} {4}"'.format(method, url, at_index,
                                             request.method, request.url)
                )
        if body is not None:
            content_type = request.headers.get(
                'content-type', 'application/octet-stream')
            if content_type.startswith('application/json'):
                decoded = json.loads(request.body, encoding='utf-8')
                if decoded != body:
                    raise AssertionError(
                        'expected body {0}, got {1}'.format(body, decoded))
            else:
                raise AssertionError('cannot decode {0}'.format(content_type))


class CreateStorageLayerTestCase(
        RequestMixin, PatchingMixin, ActArrangeAssertTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.add_json_response(
            'GET', 'http://localhost:7474/db/data',
            {'indexes': 'http://index-url/'},
        )
        cls.create_patch('familytree.storage.sqlite3.connect')

    @classmethod
    def action(cls):
        cls.storage = storage.StorageLayer(mock.sentinel.storage_name)

    def should_get_neo_action_list(self):
        self.assert_that_http_request_made(
            'http://localhost:7474/db/data', at_index=0)

    def should_request_index_list(self):
        self.assert_that_http_request_made('http://index-url/')


class WhenCreatingStorageAndPersonLabelIsMissing(CreateStorageLayerTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.add_json_response('GET', 'http://index-url/', [])

    def should_create_person_label(self):
        self.assert_that_http_request_made(
            'http://index-url/Person',
            method='POST',
            body={'property_keys': ['external_id']},
        )
