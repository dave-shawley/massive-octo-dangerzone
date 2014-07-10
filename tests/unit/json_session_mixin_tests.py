from unittest import mock
import datetime

from familytree import storage

from .. import ActArrangeAssertTestCase, PatchingMixin


########################################################################
# JsonSessionMixin._normalize_date
########################################################################

class JsonSessionMixinNormalizeDateTestCase(ActArrangeAssertTestCase):

    @classmethod
    def action(cls):
        cls.result = storage.JsonSessionMixin._normalize_date(cls.input)


class WhenJsonSessionMixinNormalizesDateTime(
        JsonSessionMixinNormalizeDateTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.input = datetime.datetime.utcnow()
        if cls.input.second == 0:
            cls.input = cls.input.replace(second=12)
        if cls.input.microsecond == 0:
            cls.input = cls.input.replace(microsecond=1234)

    def should_return_values_as_list(self):
        assert self.result == [
            self.input.year,
            self.input.month,
            self.input.day,
            self.input.hour,
            self.input.minute,
            0,
        ]


class WhenJsonSessionMixinNormalizesDate(
        JsonSessionMixinNormalizeDateTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.input = datetime.date.today()

    def should_return_values_as_list(self):
        assert self.result == [
            self.input.year, self.input.month, self.input.day]


class WhenJsonSessionMixinNormalizesAnythingElse(
        JsonSessionMixinNormalizeDateTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.input = object()

    def should_return_stringified_input(self):
        assert self.result == str(self.input)


########################################################################
# JsonSessionMixin.request
########################################################################

class JsonSessionMixinRequestTestCase(
        PatchingMixin, ActArrangeAssertTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        super_lookup = cls.create_patch(
            'familytree.storage.super', create=True)
        cls.super_request = super_lookup.return_value.request
        cls.mixin = storage.JsonSessionMixin()

    @property
    def request_method(self):
        positional, _ = self.super_request.call_args_list[0]
        return positional[0]

    @property
    def request_url(self):
        positional, _ = self.super_request.call_args_list[0]
        return positional[1]

    @property
    def request_headers(self):
        _, kwargs = self.super_request.call_args_list[0]
        return kwargs.get('headers')

    @property
    def request_data(self):
        _, kwargs = self.super_request.call_args_list[0]
        return kwargs.get('data')

    def should_call_super_request(self):
        assert self.super_request.called

    def should_call_super_request_with_method(self):
        assert self.request_method == mock.sentinel.method

    def should_call_super_request_with_url(self):
        assert self.request_url == mock.sentinel.url

    def should_return_super_response(self):
        assert self.response == self.super_request.return_value


class WhenJsonSessionMixinSendsRequest(JsonSessionMixinRequestTestCase):

    @classmethod
    def action(cls):
        cls.response = cls.mixin.request(
            mock.sentinel.method, mock.sentinel.url)

    def should_insert_accept_header(self):
        assert self.request_headers['Accept'] == 'application/json'


class JsonSessionMixinRequestWithDataTestCase(
        WhenJsonSessionMixinSendsRequest):

    @classmethod
    def arrange(cls):
        super().arrange()
        json_patch = cls.create_patch('familytree.storage.json')
        cls.json_dumps = json_patch.dumps
        cls.data = mock.Mock()

    @classmethod
    def action(cls):
        cls.response = cls.mixin.request(
            mock.sentinel.method, mock.sentinel.url, data=cls.data)


class WhenJsonSessionMixinSendsRequestWithData(
        JsonSessionMixinRequestWithDataTestCase):

    def should_jsonify_data(self):
        self.json_dumps.assert_called_once_with(
            self.data, default=self.mixin._normalize_date)

    def should_add_content_type(self):
        expected = 'application/json; charset=utf-8'
        assert self.request_headers['Content-Type'] == expected

    def should_send_jsonified_data(self):
        assert self.request_data == self.json_dumps.return_value


class WhenJsonSessionMixinSendsRequestWithContentType(
        JsonSessionMixinRequestWithDataTestCase):

    @classmethod
    def action(cls):
        cls.response = cls.mixin.request(
            mock.sentinel.method,
            mock.sentinel.url,
            data=cls.data,
            headers={'Content-Type': 'application/yaml'},
        )

    def should_not_jsonify_data(self):
        assert not self.json_dumps.called

    def should_retain_content_type_header(self):
        assert self.request_headers['Content-Type'] == 'application/yaml'

    def should_retain_request_data(self):
        assert self.request_data == self.data


class WhenJsonSessionMixinSendsRequestWithCustomJsonContentType(
        JsonSessionMixinRequestWithDataTestCase):

    @classmethod
    def action(cls):
        cls.response = cls.mixin.request(
            mock.sentinel.method,
            mock.sentinel.url,
            data=cls.data,
            headers={'Content-Type': 'application/foo+json; charset=us-ascii'},
        )

    def should_jsonify_data(self):
        self.json_dumps.assert_called_once_with(
            self.data, default=self.mixin._normalize_date)

    def should_retain_content_type_header(self):
        expected = 'application/foo+json; charset=us-ascii'
        assert self.request_headers['Content-Type'] == expected


class WhenJsonSessionMixinSendsRequestWithAcceptHeader(
        JsonSessionMixinRequestTestCase):

    @classmethod
    def action(cls):
        cls.response = cls.mixin.request(
            mock.sentinel.method,
            mock.sentinel.url,
            headers={'accept': 'application/familytree+json; version=1'},
        )

    def should_retain_accept_header(self):
        expected = 'application/familytree+json; version=1'
        assert self.request_headers['Accept'] == expected
