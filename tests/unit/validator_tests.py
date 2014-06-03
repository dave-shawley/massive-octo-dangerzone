from unittest import mock

import py.test

from familytree.cli import validators
from .. import RandomValueMixin


class WhenValidatingAges(RandomValueMixin):

    def should_return_simple_floats(self):
        assert validators.age(self.random_int) == float(self.last_random)

    def should_handle_month_based_ages(self):
        assert validators.age('1/12') == (1.0 / 12.0)

    def should_fail_on_non_number(self):
        py.test.raises(
            validators.ValidationError, validators.age, self.random_string)


class WhenValidatingDate:

    def setup(self):
        self._patcher = mock.patch('familytree.cli.validators.datetime')
        self.strptime = self._patcher.start().strptime

    def teardown(self):
        self._patcher.stop()

    @property
    def validator(self):
        return validators.date(mock.sentinel.format)

    def should_return_callable(self):
        assert callable(self.validator)

    def should_delegate_to_strptime(self):
        self.validator(mock.sentinel.value)
        self.strptime.assert_called_once_with(mock.sentinel.value,
                                              mock.sentinel.format)

    def should_return_only_date_portion(self):
        assert (self.validator(mock.sentinel.value)
                == self.strptime.return_value.date.return_value)

    def should_raise_validation_error_on_failure(self):
        self.strptime.side_effect = [ValueError]
        py.test.raises(validators.ValidationError,
                       self.validator, mock.sentinel.value)


class WhenValidatingGender(RandomValueMixin):

    def should_accept_male_abbreviation(self):
        assert validators.gender('m') == 'male'
        assert validators.gender('M') == 'male'

    def should_accept_male_string(self):
        assert validators.gender('male') == 'male'
        assert validators.gender('Male') == 'male'

    def should_accept_female_abbreviation(self):
        assert validators.gender('f') == 'female'
        assert validators.gender('F') == 'female'

    def should_accept_female_string(self):
        assert validators.gender('female') == 'female'
        assert validators.gender('Female') == 'female'

    def should_reject_other_values(self):
        py.test.raises(validators.ValidationError,
                       validators.gender, self.random_string)


class WhenValidatingYesNo(RandomValueMixin):

    def should_accept_yes_string(self):
        assert validators.yes_no('yes') is True

    def should_accept_yes_abbreviation(self):
        assert validators.yes_no('y') is True
        assert validators.yes_no('Y') is True

    def should_accept_no_string(self):
        assert validators.yes_no('no') is False

    def should_accept_no_abbreviation(self):
        assert validators.yes_no('n') is False
        assert validators.yes_no('N') is False

    def should_reject_other_strings(self):
        py.test.raises(validators.ValidationError,
                       validators.yes_no, self.random_string)


class WhenValidatingFamilialRelationship(RandomValueMixin):

    def should_accept_head_of_house(self):
        assert validators.familial_relation('head of house') == 'head of house'
        assert validators.familial_relation('head-of-house') == 'head of house'
        assert validators.familial_relation('Head-of-House') == 'head of house'
        assert validators.familial_relation('head') == 'head of house'
        assert validators.familial_relation('H') == 'head of house'

    def should_accept_son(self):
        assert validators.familial_relation('son') == 'son'
        assert validators.familial_relation('Son') == 'son'
        assert validators.familial_relation('s/o') == 'son'

    def should_accept_son_in_law(self):
        assert validators.familial_relation('son-in-law') == 'son in law'
        assert validators.familial_relation('son in law') == 'son in law'
        assert validators.familial_relation('sil') == 'son in law'
        assert validators.familial_relation('SIL') == 'son in law'

    def should_accept_daughter(self):
        assert validators.familial_relation('daughter') == 'daughter'
        assert validators.familial_relation('Daughter') == 'daughter'
        assert validators.familial_relation('d/o') == 'daughter'

    def should_accept_daughter_in_law(self):
        assert (validators.familial_relation('daughter-in-law')
                == 'daughter in law')
        assert (validators.familial_relation('daughter in law')
                == 'daughter in law')
        assert validators.familial_relation('dil') == 'daughter in law'
        assert validators.familial_relation('DIL') == 'daughter in law'

    def should_accept_wife(self):
        assert validators.familial_relation('wife') == 'wife'
        assert validators.familial_relation('Wife') == 'wife'
        assert validators.familial_relation('w/o') == 'wife'

    def should_accept_husband(self):
        assert validators.familial_relation('husband') == 'husband'
        assert validators.familial_relation('Husband') == 'husband'
        assert validators.familial_relation('h/o') == 'husband'

    def should_reject_other_values(self):
        py.test.raises(validators.ValidationError,
                       validators.familial_relation, self.random_string)
