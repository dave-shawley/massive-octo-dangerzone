from unittest import mock

import py.test

from familytree.cli import console, validators
from .. import ActArrangeAssertTestCase, PatchingMixin


class PromptTestCase:
    _input_patch = mock.patch('familytree.cli.console.input', create=True)

    def setup(self):
        self.input_mock = self._input_patch.start()
        self.prompt_string = mock.MagicMock(spec=str)

    def teardown(self):
        self._input_patch.stop()

    def prompt(self, **kwargs):
        return console.prompt(self.prompt_string, **kwargs)

    @property
    def input_return_value(self):
        return self.input_mock.return_value.strip.return_value


class WhenPrompting(PromptTestCase):

    def should_read_input(self):
        self.prompt()
        self.input_mock.assert_called_once_with(mock.ANY)

    def should_return_stripped_output(self):
        assert self.prompt() == self.input_return_value

    def should_retry_until_input_is_not_empty(self):
        self.input_mock.side_effect = ['', '      ', 'nonempty']
        assert self.prompt() == 'nonempty'
        assert self.input_mock.call_count == 3

    def should_exit_on_ctrl_c(self):
        self.input_mock.side_effect = KeyboardInterrupt
        py.test.raises(SystemExit, self.prompt)

    def should_exit_on_eof(self):
        self.input_mock.side_effect = EOFError
        py.test.raises(SystemExit, self.prompt)


class WhenPromptingAndAllowEmptyIsTrue(PromptTestCase):

    def should_allow_empty_strings(self):
        self.input_mock.return_value = ''
        assert self.prompt(allow_empty=True) == ''


class WhenPromptingWithValidator(PromptTestCase):

    def setup(self):
        super().setup()
        self.validator = mock.Mock()

    def prompt(self, **kwargs):
        return console.prompt(
            self.prompt_string,
            validator=self.validator,
            **kwargs
        )

    def should_use_validator_when_present(self):
        self.prompt()
        self.validator.assert_called_once_with(self.input_return_value)

    def should_return_validator_results(self):
        assert self.prompt() == self.validator.return_value

    def should_retry_until_validator_succeeds(self):
        self.validator.side_effect = [ValueError, ValueError, 'success']
        assert self.prompt() == 'success'
        assert self.validator.call_count == 3

    def should_invoke_validator_with_empty_string(self):
        self.input_mock.return_value = ''
        self.prompt(allow_empty=True)
        self.validator.assert_called_once_with('')

    def should_not_allow_empty_strings_to_be_returned(self):
        self.validator.side_effect = ['', 'nonempty']
        self.prompt()
        assert self.validator.call_count == 2

    def should_allow_empty_return_values_when_configured(self):
        self.validator.return_value = ''
        assert self.prompt(allow_empty=True) == ''


class WhenPromptingAndNoneOnEmptyIsTrue(PromptTestCase):

    def should_return_none_when_input_is_empty(self):
        self.input_mock.return_value = ''
        assert self.prompt(none_on_empty=True) is None


class WhenPromptingAndNoneOnEofIsTrue(PromptTestCase):

    def should_return_none_when_eof_occurs(self):
        self.input_mock.side_effect = EOFError
        assert self.prompt(none_on_eof=True) is None


class SimplePatchedPromptTestCase(PatchingMixin, ActArrangeAssertTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.prompt_mock = cls.create_patch('familytree.cli.console.prompt')
        cls.kwargs = {'some-arg': mock.sentinel.kwarg_value}

    def should_pass_prompt_safely(self):
        self.prompt_mock.assert_called_once_with(
            '{0}', mock.sentinel.prompt, validator=mock.ANY, **self.kwargs)

    def should_return_result_from_prompt(self):
        assert self.returned == self.prompt_mock.return_value


class WhenAskingYesNoQuestion(SimplePatchedPromptTestCase):

    @classmethod
    def action(cls):
        cls.returned = console.ask_yes_no(mock.sentinel.question, **cls.kwargs)

    def should_pass_prompt_safely(self):
        self.prompt_mock.assert_called_once_with(
            '{0}? [yn]', mock.sentinel.question,
            validator=mock.ANY, **self.kwargs)

    def should_use_yes_no_validator(self):
        self.prompt_mock.assert_called_once_with(
            mock.ANY, mock.sentinel.question,
            validator=validators.yes_no, **self.kwargs)


class WhenGettingAnAge(SimplePatchedPromptTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.kwargs.clear()  # **kwargs unused by get_age()

    @classmethod
    def action(cls):
        cls.returned = console.get_age(mock.sentinel.prompt)

    def should_call_prompt_with_validator(self):
        self.prompt_mock.assert_called_once_with(
            mock.ANY, mock.ANY, validator=validators.age)


class WhenGettingDate(SimplePatchedPromptTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.date_validator = cls.create_patch('familytree.cli.validators.date')

    @classmethod
    def action(cls):
        cls.returned = console.get_date(
            mock.sentinel.prompt, mock.sentinel.date_format, **cls.kwargs)

    def should_create_date_validator(self):
        self.date_validator.assert_called_once_with(mock.sentinel.date_format)

    def should_call_prompt_with_validator(self):
        self.prompt_mock.assert_called_once_with(
            mock.ANY, mock.ANY,
            validator=self.date_validator.return_value, **self.kwargs)


class WhenGettingGender(SimplePatchedPromptTestCase):

    @classmethod
    def action(cls):
        cls.returned = console.get_gender(**cls.kwargs)

    def should_pass_prompt_safely(self):
        self.prompt_mock.assert_called_once_with(
            'Gender', validator=mock.ANY, **self.kwargs)

    def should_call_prompt_with_validator(self):
        self.prompt_mock.assert_called_once_with(
            mock.ANY, validator=validators.gender, **self.kwargs)


class WhenGettingLocation(PatchingMixin, ActArrangeAssertTestCase):

    @staticmethod
    def prompt_fixture(prompt, *args, **kwargs):
        return {
            '{0} place': mock.sentinel.entered_place,
            '{0} county': mock.sentinel.entered_county,
            '{0} state': mock.sentinel.entered_state,
        }[prompt]

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.prompt_mock = cls.create_patch(
            'familytree.cli.console.prompt', side_effect=cls.prompt_fixture)

    @classmethod
    def action(cls):
        cls.returned = console.get_location(mock.sentinel.prefix)

    def should_prompt_for_place(self):
        self.prompt_mock.assert_any_call('{0} place', mock.sentinel.prefix)

    def should_prompt_for_county(self):
        self.prompt_mock.assert_any_call(
            '{0} county', mock.sentinel.prefix, allow_empty=True)

    def should_prompt_for_state(self):
        self.prompt_mock.assert_any_call(
            '{0} state', mock.sentinel.prefix, allow_empty=True)

    def should_return_location_dict(self):
        assert self.returned == {
            'place': mock.sentinel.entered_place,
            'county': mock.sentinel.entered_county,
            'state': mock.sentinel.entered_state,
            'country': 'USA',
        }


class WhenShowingOutput(PatchingMixin, ActArrangeAssertTestCase):

    @classmethod
    def arrange(cls):
        super().arrange()
        cls.mock_print = cls.create_patch(
            'familytree.cli.console.print', create=True)
        cls.display_format = mock.Mock()
        cls.args = [mock.sentinel.first_arg, mock.sentinel.next_arg]

    @classmethod
    def action(cls):
        console.show(cls.display_format, *cls.args)

    def should_format_arguments(self):
        self.display_format.format.assert_called_once_with(*self.args)

    def should_print_output(self):
        self.mock_print.assert_called_once_with(
            self.display_format.format.return_value)
