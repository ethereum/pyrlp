import pytest

from eth_utils import (
    decode_hex,
)

from rlp.exceptions import DecodingError
from rlp.codec import consume_length_prefix, consume_item
from rlp import (
    decode,
    encode,
)


EMPTYLIST = encode([])


def compare_length(rlpdata, length):
    _, _typ, _len, _pos = consume_length_prefix(rlpdata, 0)
    assert _typ is list
    lenlist = 0
    if rlpdata == EMPTYLIST:
        return -1 if length > 0 else 1 if length < 0 else 0
    while 1:
        if lenlist > length:
            return 1
        _, _, _l, _p = consume_length_prefix(rlpdata, _pos)
        lenlist += 1
        if _l + _p >= len(rlpdata):
            break
        _pos = _l + _p
    return 0 if lenlist == length else -1


def test_compare_length():
    data = encode([1, 2, 3, 4, 5])
    assert compare_length(data, 100) == -1
    assert compare_length(data, 5) == 0
    assert compare_length(data, 1) == 1

    data = encode([])
    assert compare_length(data, 100) == -1
    assert compare_length(data, 0) == 0
    assert compare_length(data, -1) == 1


def test_favor_short_string_form():
    data = decode_hex('b8056d6f6f7365')
    with pytest.raises(DecodingError):
        decode(data)

    data = decode_hex('856d6f6f7365')
    assert decode(data) == b'moose'


def test_consume_item():
    obj = [b'f', b'bar', b'a' * 100, 105, [b'nested', b'list']]
    rlp = encode(obj)
    item, per_item_rlp, end = consume_item(rlp, 0)
    assert per_item_rlp == [
        (b'\xf8y' b'f' + b'\x83bar' + b'\xb8d' + b'a' * 100 + b'i' +
         b'\xcc\x86nested\x84list'),
        [b'f'],
        [b'\x83bar'],
        [b'\xb8d' + b'a' * 100],
        [b'i'],
        [b'\xcc\x86nested\x84list', [b'\x86nested'], [b'\x84list']]
    ]
    assert end == 123
    assert per_item_rlp[0] == rlp
