# -*- coding: utf8 -*-
import struct

import rlp


def test_bytearray():
    e = rlp.encode('abc')
    d = rlp.decode(e)
    d = rlp.decode(bytearray(e))


def test_bytearray_lazy():
    e = rlp.encode('abc')
    d = rlp.decode(e)
    d = rlp.decode_lazy(bytearray(e))


def test_bytearray_encode_decode():
    value = bytearray(b'asdf')
    encoded = rlp.utils.encode_hex(value)
    decoded = rlp.utils.decode_hex(encoded)

    assert value == decoded


def test_big_endian_to_int():
    assert rlp.utils.big_endian_to_int('\x00') == 0
    assert rlp.utils.big_endian_to_int(bytearray('\x00')) == 0

    value = struct.pack('>Q', 3141516)
    assert rlp.utils.big_endian_to_int(value) == 3141516
    assert rlp.utils.big_endian_to_int(bytearray(value)) == 3141516
