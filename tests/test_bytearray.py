# -*- coding: utf8 -*-
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


def test_encoding_bytearray():
    s = str_to_bytes('abcdef')
    direct = encode(s)
    from_bytearray = encode(bytearray(s))
    assert direct == from_bytearray
    assert decode(direct) == s
