# -*- coding: UTF-8 -*-
from hypothesis import (
    given,
    strategies as st,
)
import pytest

from rlp import (
    DeserializationError,
    SerializationError,
    decode,
    encode,
)
from rlp.sedes import (
    Text,
)


@pytest.mark.parametrize(
    "value,expected",
    (
        ("", b""),
        ("asdf", b"asdf"),
        ("fdsa", b"fdsa"),
        ("�", b"\xef\xbf\xbd"),
        ("", b"\xc2\x80"),
        ("ࠀ", b"\xe0\xa0\x80"),
        ("𐀀", b"\xf0\x90\x80\x80"),
        ("�����", b"\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd"),
        (
            "������",
            b"\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd",
        ),
    ),
)
def test_simple_text_serialization(value, expected):
    sedes = Text()
    assert sedes.serialize(value) == expected


@pytest.mark.parametrize(
    "value",
    (
        b"",
        b"arst",
        1,
        True,
        None,
        1.0,
        bytearray(),
    ),
)
def test_unserializable_text_sedes_values(value):
    sedes = Text()
    with pytest.raises(SerializationError):
        sedes.serialize(value)


@pytest.mark.parametrize(
    "length,value,expected",
    (
        (0, "", b""),
        (1, "a", b"a"),
        (1, "a", b"a"),
        (1, "�", b"\xef\xbf\xbd"),
        (1, "", b"\xc2\x80"),
        (1, "ࠀ", b"\xe0\xa0\x80"),
        (1, "𐀀", b"\xf0\x90\x80\x80"),
    ),
)
def test_fixed_length_text_serialization(length, value, expected):
    sedes = Text.fixed_length(length)
    assert sedes.serialize(value) == expected


@pytest.mark.parametrize(
    "length,value",
    (
        (1, ""),
        (0, "a"),
        (2, "a"),
        (2, "a"),
        (2, "�"),
        (4, "�"),  # actual binary length
        (2, ""),
        (4, ""),  # actual binary length
        (2, "ࠀ"),
        (4, "ࠀ"),  # actual binary length
        (2, "𐀀"),
        (4, "𐀀"),  # actual binary length
        (4, "�����"),
        (15, "�����"),  # actual binary length
        (5, "������"),
        (18, "������"),  # actual binary length
    ),
)
def test_fixed_length_text_serialization_with_wrong_length(length, value):
    sedes = Text.fixed_length(length)
    with pytest.raises(SerializationError):
        sedes.serialize(value)


@pytest.mark.parametrize(
    "min_length,max_length,value,expected",
    (
        (0, 4, "", b""),
        (0, 4, "arst", b"arst"),
        (0, 4, "arst", b"arst"),
        (0, 4, "arst", b"arst"),
        (0, 1, "�", b"\xef\xbf\xbd"),
        (0, 1, "", b"\xc2\x80"),
        (0, 1, "ࠀ", b"\xe0\xa0\x80"),
        (0, 1, "𐀀", b"\xf0\x90\x80\x80"),
        (
            0,
            5,
            "�����",
            b"\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd",
        ),
        (
            0,
            6,
            "������",
            b"\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd",
        ),  # noqa: E501
    ),
)
def test_min_max_length_text_serialization(min_length, max_length, value, expected):
    sedes = Text(min_length=min_length, max_length=max_length)
    assert sedes.serialize(value) == expected


@pytest.mark.parametrize(
    "min_length,max_length,value",
    (
        (1, 4, ""),
        (5, 6, ""),
        (1, 3, "arst"),
        (5, 6, "arst"),
        (2, 3, "�"),
        (4, 5, ""),
        (6, 7, "ࠀ"),
        (8, 9, "𐀀"),
        (6, 9, "�����"),
        (0, 4, "������"),
    ),
)
def test_min_max_length_text_serialization_wrong_length(min_length, max_length, value):
    sedes = Text(min_length=min_length, max_length=max_length)
    with pytest.raises(SerializationError):
        sedes.serialize(value)


@pytest.mark.parametrize(
    "serial,expected",
    (
        (b"", ""),
        (b"asdf", "asdf"),
        (b"fdsa", "fdsa"),
        (b"\xef\xbf\xbd", "�"),
        (b"\xc2\x80", ""),
        (b"\xe0\xa0\x80", "ࠀ"),
        (b"\xf0\x90\x80\x80", "𐀀"),
        (b"\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd", "�����"),
        (
            b"\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd",
            "������",
        ),
    ),
)
def test_deserialization_text_sedes(serial, expected):
    sedes = Text()
    assert sedes.deserialize(serial) == expected


def test_allow_empty_bypasses_length_checks():
    sedes = Text.fixed_length(1, allow_empty=True)
    assert sedes.serialize("") == b""

    with pytest.raises(SerializationError):
        sedes.serialize(b"12")


@given(value=st.text())
def test_round_trip_text_encoding_and_decoding(value):
    sedes = Text()
    encoded = encode(value, sedes=sedes)
    actual = decode(encoded, sedes=sedes)
    assert actual == value


def test_desirialization_of_text_encoding_failure():
    sedes = Text()
    with pytest.raises(DeserializationError):
        sedes.deserialize(b"\xff")
