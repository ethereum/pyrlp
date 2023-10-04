# -*- coding: UTF-8 -*-
import pytest

from rlp import (
    SerializationError,
)
from rlp.sedes import (
    Binary,
)


@pytest.mark.parametrize(
    "value,expected",
    (
        (b"", b""),
        (b"asdf", b"asdf"),
        (b"\x00" * 20, b"\x00" * 20),
        (b"fdsa", b"fdsa"),
    ),
)
def test_simple_binary_serialization(value, expected):
    sedes = Binary()
    assert sedes.serialize(value) == expected


@pytest.mark.parametrize(
    "value",
    ([], 5, str, "", "arst"),
)
def test_binary_unserializable_values(value):
    sedes = Binary()
    with pytest.raises(SerializationError):
        sedes.serialize(value)


@pytest.mark.parametrize(
    "value,expected",
    (
        (b"asdfg", b"asdfg"),
        (b"\x00\x01\x02\x03\x04", b"\x00\x01\x02\x03\x04"),
        (b"ababa", b"ababa"),
    ),
)
def test_binary_fixed_length_serialization(value, expected):
    sedes = Binary.fixed_length(5)
    assert sedes.serialize(value) == expected


def test_binary_fixed_lenght_of_zero():
    sedes = Binary.fixed_length(0)
    assert sedes.serialize(b"") == b""

    with pytest.raises(SerializationError):
        sedes.serialize(b"a")
    with pytest.raises(SerializationError):
        sedes.serialize(b"arst")


@pytest.mark.parametrize(
    "value",
    (b"asdf", b"asdfgh", b"", b"bababa"),
)
def test_binary_fixed_length_serialization_with_wrong_length(value):
    sedes = Binary.fixed_length(5)
    with pytest.raises(SerializationError):
        sedes.serialize(value)


@pytest.mark.parametrize(
    "value,expected",
    (
        (b"as", b"as"),
        (b"dfg", b"dfg"),
        (b"hjkl", b"hjkl"),
        (b"\x00\x01\x02", b"\x00\x01\x02"),
    ),
)
def test_binary_variable_length_serialization(value, expected):
    sedes = Binary(2, 4)
    assert sedes.serialize(value) == expected


@pytest.mark.parametrize(
    "value",
    (b"", b"a", b"abcde"),
)
def test_binary_variable_length_serialization_wrong_length(value):
    sedes = Binary(2, 4)
    with pytest.raises(SerializationError):
        sedes.serialize(value)


@pytest.mark.parametrize(
    "value,expected",
    (
        (b"abc", b"abc"),
        (b"abcd", b"abcd"),
        (b"x" * 132, b"x" * 132),
    ),
)
def test_binary_min_length_serialization(value, expected):
    sedes = Binary(min_length=3)
    assert sedes.serialize(value) == expected


@pytest.mark.parametrize(
    "value",
    (b"ab", b"", b"a", b"xy"),
)
def test_binary_min_length_serialization_wrong_length(value):
    sedes = Binary(min_length=3)
    with pytest.raises(SerializationError):
        sedes.serialize(value)


@pytest.mark.parametrize(
    "value,expected",
    (
        (b"", b""),
        (b"ab", b"ab"),
        (b"abc", b"abc"),
    ),
)
def test_binary_max_length_serialization(value, expected):
    sedes = Binary(max_length=3)
    assert sedes.serialize(value) == expected


@pytest.mark.parametrize(
    "value",
    (b"abcd", b"vwxyz", b"a" * 32),
)
def test_binary_max_length_serialization_wrong_length(value):
    sedes = Binary(max_length=3)
    with pytest.raises(SerializationError):
        sedes.serialize(value)


@pytest.mark.parametrize(
    "value,expected",
    (
        (b"", b""),
        (b"abc", b"abc"),
        (b"abcd", b"abcd"),
        (b"abcde", b"abcde"),
    ),
)
def test_binary_min_and_max_length_with_allow_empty(value, expected):
    sedes = Binary(min_length=3, max_length=5, allow_empty=True)
    assert sedes.serialize(value) == expected


@pytest.mark.parametrize(
    "value",
    (b"a", b"ab", b"abcdef", b"abcdefgh" * 10),
)
def test_binary_min_and_max_length_with_allow_empty_wrong_length(value):
    sedes = Binary(min_length=3, max_length=5, allow_empty=True)
    with pytest.raises(SerializationError):
        sedes.serialize(value)
