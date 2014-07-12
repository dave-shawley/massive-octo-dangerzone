import datetime
import hashlib
import math

from familytree import storage


def verify(obj, linear_form):
    hashed = storage.generate_hash('Object Type', obj)
    prefixed = 'object type#{0}'.format(linear_form)
    assert hashed == hashlib.sha1(prefixed.encode('utf-8')).hexdigest()


def should_lowercase_string_values():
    verify(
        {'str': 'A String'},
        '{str=a string}',
    )


def should_format_integers():
    verify(
        {'simple': 1234, 'long': 0xDEADCAFEBABE},
        '{long=244838016400062,simple=1234}',
    )


def should_handle_odd_floats():
    verify(
        {'simple': math.pi, 'hard': float('inf'), 'harder': 1j},
        '{hard=inf,harder=1j,simple=%s}' % math.pi,
    )


def should_format_dates_as_iso8601():
    today = datetime.date.today()
    verify(
        {'date': today},
        '{date=%s}' % today.isoformat(),
    )


def should_format_datetime_as_iso8601_without_subseconds():
    now = datetime.datetime.utcnow().replace(microsecond=12345)
    verify(
        {'datetime': now},
        '{datetime=%s}' % now.replace(microsecond=0).isoformat(),
    )


def should_bracket_embedded_lists():
    verify(
        {'a list': ['one', 2, 'Three']},
        '{a list=[one,2,three]}',
    )


def should_bracket_embedded_tuples():
    verify(
        {'a tuple': ('one', 2, 'Three')},
        '{a tuple=[one,2,three]}',
    )


def should_bracket_embedded_generators():
    def genny():
        yield 'one'
        yield 2
        yield 'Three'

    verify(
        {'a generator': genny()},
        '{a generator=[one,2,three]}',
    )


def should_brace_embedded_dicts():
    verify(
        {'a dict': {'key': 'Value'}},
        '{a dict={key=value}}',
    )
