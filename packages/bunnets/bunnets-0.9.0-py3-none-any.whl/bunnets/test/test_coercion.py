from datetime import datetime
from enum import Enum

from pytest import raises

from bunnets import coerce_type
from bunnets.error import InvalidInputError


def test_coercion_basic():
    input_val = "True"
    coerce_to = bool
    expected = True

    actual = coerce_type(input_val, coerce_to)

    assert actual == expected


def test_coercion_type():
    input_val = "True"
    coerce_to = bool

    actual = coerce_type(input_val, coerce_to)

    assert isinstance(actual, coerce_to)


def test_coercion_bool_unknown():
    input_val = "blort"
    coerce_to = bool
    expected = None

    actual = coerce_type(input_val, coerce_to)

    assert actual == expected


def test_coercion_dt_good():
    input_val = "1234567890"
    coerce_to = datetime
    expected = datetime(year=2009, month=2, day=13, hour=23, minute=31, second=30)

    actual = coerce_type(input_val, coerce_to)

    assert actual == expected


def test_coercion_dt_bad():
    input_val = "one two three four five six seven eight nine zero"
    coerce_to = datetime

    with raises(InvalidInputError):
        coerce_type(input_val, coerce_to, True)


def test_coercion_enum_good():
    class TestEnum(Enum):
        ONE = 1
        UNO = 1
        TWO = 2
        DOS = 2

    coerce_to = TestEnum
    expected = [
        TestEnum.ONE,
        TestEnum.ONE,
        TestEnum.UNO,
        TestEnum.ONE,
        TestEnum.ONE,
    ]

    actual = [
        coerce_type("ONE", coerce_to),
        coerce_type("one", coerce_to),
        coerce_type("Uno", coerce_to),
        coerce_type("1", coerce_to),
        coerce_type(1, coerce_to),
    ]

    assert actual == expected
