# -*- coding: utf8 -*-
from eth_utils import (
    encode_hex,
    decode_hex,
)

from rlp import (
    encode,
    decode,
    decode_lazy,
)
from rlp.utils import str_to_bytes


def test_bytearray():
    e = encode('abc')
    expected = decode(e)
    actual = decode(bytearray(e))
    assert actual == expected


def test_bytearray_lazy():
    e = encode('abc')
    expected = decode(e)
    actual = decode_lazy(bytearray(e))
    assert expected == actual


def test_bytearray_encode_decode():
    value = bytearray(b'asdf')
    encoded = encode_hex(value)
    decoded = decode_hex(encoded)

    assert value == decoded


def test_encoding_bytearray():
    s = str_to_bytes('abcdef')
    direct = encode(s)
    from_bytearray = encode(bytearray(s))
    assert direct == from_bytearray
    assert decode(direct) == s
