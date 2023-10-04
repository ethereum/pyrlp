import pytest

from rlp import (
    DecodingError,
    decode,
)

invalid_rlp = (
    b"",
    b"\x00\xab",
    b"\x00\x00\xff",
    b"\x83dogcat",
    b"\x83do",
    b"\xc7\xc0\xc1\xc0\xc3\xc0\xc1\xc0\xff",
    b"\xc7\xc0\xc1\xc0\xc3\xc0\xc1" b"\x81\x02",
    b"\xb8\x00",
    b"\xb9\x00\x00",
    b"\xba\x00\x02\xff\xff",
    b"\x81\x54",
)


def test_invalid_rlp():
    for serial in invalid_rlp:
        with pytest.raises(DecodingError):
            decode(serial)
