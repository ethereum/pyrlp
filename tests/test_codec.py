import pytest

from eth_utils import (
    decode_hex,
)

from rlp.exceptions import DecodingError
from rlp import (
    decode,
    encode,
    compare_length,
)


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
