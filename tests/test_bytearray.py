# -*- coding: utf8 -*-
from rlp import (
    decode,
    decode_lazy,
    encode,
)


def test_bytearray():
    e = encode(b"abc")
    expected = decode(e)
    actual = decode(bytearray(e))
    assert actual == expected


def test_bytearray_lazy():
    e = encode(b"abc")
    expected = decode(e)
    actual = decode_lazy(bytearray(e))
    assert expected == actual


def test_encoding_bytearray():
    s = b"abcdef"
    direct = encode(s)
    from_bytearray = encode(bytearray(s))
    assert direct == from_bytearray
    assert decode(direct) == s
