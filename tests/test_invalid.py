import pytest
from rlp import decode, DecodingError


invalid_rlp = (
    '',
    '\x00\xab',
    '\x00\x00\xff',
    '\x83dogcat',
    '\x83do',
    '\xc7\xc0\xc1\xc0\xc3\xc0\xc1\xc0\xff',
    '\xc7\xc0\xc1\xc0\xc3\xc0\xc1'
)


def test_invalid_rlp():
    for serial in invalid_rlp:
        with pytest.raises(DecodingError):
            decode(serial)
