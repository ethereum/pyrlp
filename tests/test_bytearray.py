# -*- coding: utf8 -*-
import struct

import rlp


def test_bytearray():
    e = rlp.encode('abc')
    expected = rlp.decode(e)
    actual = rlp.decode(bytearray(e))
    assert expected == actual


def test_bytearray_lazy():
    e = rlp.encode('abc')
    expected = rlp.decode(e)
    actual = rlp.decode_lazy(bytearray(e))
    assert expected == actual


def test_bytearray_encode_decode():
    value = bytearray(b'asdf')
    encoded = rlp.utils.encode_hex(value)
    decoded = rlp.utils.decode_hex(encoded)

    assert value == decoded


def test_big_endian_to_int():
    assert rlp.utils.big_endian_to_int(b'\x00') == 0
    assert rlp.utils.big_endian_to_int(bytearray(b'\x00')) == 0

    value = struct.pack('>Q', 3141516)
    assert rlp.utils.big_endian_to_int(value) == 3141516
    assert rlp.utils.big_endian_to_int(bytearray(value)) == 3141516


def test_encoding_bytearray():
    s = rlp.utils.str_to_bytes('abcdef')
    direct = rlp.encode(s)
    from_bytearray = rlp.encode(bytearray(s))
    assert direct == from_bytearray
    assert rlp.decode(direct) == s
