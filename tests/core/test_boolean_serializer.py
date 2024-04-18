import pytest

from rlp import (
    DeserializationError,
    SerializationError,
)
from rlp.sedes import (
    Boolean,
)


@pytest.mark.parametrize(
    "value,expected",
    (
        (True, b"\x01"),
        (False, b""),
    ),
)
def test_boolean_serialize_values(value, expected):
    sedes = Boolean()
    assert sedes.serialize(value) == expected


@pytest.mark.parametrize(
    "value",
    (
        None,
        1,
        0,
        "True",
        b"True",
    ),
)
def test_boolean_serialize_bad_values(value):
    sedes = Boolean()
    with pytest.raises(SerializationError):
        sedes.serialize(value)


@pytest.mark.parametrize(
    "value,expected",
    (
        (b"\x01", True),
        (b"", False),
    ),
)
def test_boolean_deserialization(value, expected):
    sedes = Boolean()
    assert sedes.deserialize(value) == expected


@pytest.mark.parametrize(
    "value",
    (
        b" ",
        b"\x02",
        b"\x00\x00",
        b"\x01\x00",
        b"\x00\x01",
        b"\x01\x01",
    ),
)
def test_boolean_deserialization_bad_value(value):
    sedes = Boolean()
    with pytest.raises(DeserializationError):
        sedes.deserialize(value)
