"""
Functions and classes related to user input validation.
-------------------------------------------------------

This module is a collection of functions and classes used by the
:mod:`user input layer <familytree.cli.console>` to validate and
transform the user input from raw strings into a more usable form.
The validation routines take the general form of a callable that
receives the user input as a ``str`` argument.  They validate that
the input matches the constraint and raise a :exc:`.ValidationError`
if it does not. If the input is good, then they may perform a type
transformation on the input before they return the sanitized input.
The following validators are defined:

- :func:`.age` - floating point number of years
- :func:`.date` - formatted :class:`~datetime.datetime` value
- :func:`.gender` - ``'male'`` or ``'female'``
- :func:`.yes_no` - :data:`True` or :data:`False`

For example, the :func:`yes_no` validator simply checks if the
case normalized input matches *yes*, *y*, *no*, or *n*.  If it
receives any other input, then it raises a :exc:`.ValidationError`.
If the input is good, then it returns a Boolean value that represents
the validated value.

"""
from datetime import datetime


class ValidationError(Exception):

    """
    A user input value failed validation.

    :keyword str message: optional message to send with the
        exception.  If this parameter is omitted, then the
        class name is used.
    :keyword Exception cause: optional exception instance to
        keep as the causal exception.
    :keyword expected: value that was expected
    :keyword value: value that was received

    Each of the keyword parameters are stored as as attributes
    with the same name.

    This exception is thrown by any of the various validation
    functions in the :mod:`familytree.cli.validators` module.
    The :mod:`familytree.cli.console` functions recognize
    failures of this form and handle them specifically.  See the
    documentation for :func:`familytree.cli.console.prompt` for
    more details.

    """

    def __init__(self, *args, **kwargs):
        self.message = kwargs.pop('message', self.__class__.__name__)
        self.cause = kwargs.pop('cause', None)
        self.expected_value = kwargs.pop('expected', None)
        self.actual_value = kwargs.pop('value', None)
        super().__init__(self.message, *args, **kwargs)

    def __str__(self):  # pragma no cover
        rest = []
        if self.cause:
            rest.append('cause={0}'.format(str(self.cause)))
        if self.expected_value:
            rest.append('expected={0}'.format(str(self.expected_value)))
        if self.actual_value:
            rest.append('actual={0}'.format(str(self.actual_value)))

        return (self.message if not rest
                else '{0}: {1}'.format(self.message, ','.join(rest)))


def age(value):
    """Verifies that ``value`` is an age.

    :return: ``value`` coerced to a :func:`float`

    If ``value`` cannot be coerced directly to a :func:`float`
    and it is a :func:`str` that ends with ``/12``, then it is
    treated as a month value (e.g., 3/12).

    """
    try:
        return float(value)
    except ValueError as error:
        if '/12' in value:
            return float(value[:value.find('/12')]) / 12.0
        raise ValidationError(cause=error)


def date(format):
    """Validate a date value.

    :param str format: passed to :meth:`datetime.datetime.strptime`
    :returns: ``callable`` that acts as a validator.

    """
    def validator(value):
        try:
            return datetime.strptime(value, format).date()
        except ValueError as error:
            raise ValidationError(cause=error)
    return validator


def gender(value):
    """Validate a gender value.

    :returns: the :func:`str` ``'male'`` or ``'female'``

    """
    if value.lower() in ('m', 'male'):
        return 'male'
    if value.lower() in ('f', 'female'):
        return 'female'
    raise ValidationError(expected='male|female', value=value)


def yes_no(value):
    """Validate a yes/no value.

    :returns: :data:`True` for *yes* and :data:`False` for *no*

    """
    if value.lower() in ('y', 'yes'):
        return True
    if value.lower() in ('n', 'no'):
        return False
    raise ValidationError(expected='yes|no', value=value)


_VALID_FAMILY_RELATIONS = {
    'daughter',
    'daughter in law',
    'head of house',
    'husband',
    'son',
    'son in law',
    'wife',
}

_RELATION_ABBREVIATIONS = {
    'd/o': 'daughter',
    'h/o': 'husband',
    's/o': 'son',
    'w/o': 'wife',
    'dil': 'daughter in law',
    'sil': 'son in law',
}


def familial_relation(value):
    """Validate and transform a familial relation.

    :return: a value from the :data:`_VALID_FAMILY_RELATIONS` set

    """
    normalized = ' '.join(value.lower().replace('-', ' ').split())
    validating = normalized

    if validating in _RELATION_ABBREVIATIONS:
        normalized = _RELATION_ABBREVIATIONS[validating]

    if normalized not in _VALID_FAMILY_RELATIONS:
        raise ValidationError(expected='familial relationship', value=value)

    return normalized
