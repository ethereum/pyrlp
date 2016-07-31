import pytest
import rlp

def test_compare_length():
    data = rlp.encode([1,2,3,4,5])
    assert rlp.compare_length(data, 100) == -1
    assert rlp.compare_length(data, 5) == 0
    assert rlp.compare_length(data, 1) == 1

    data = rlp.encode([])
    assert rlp.compare_length(data, 100) == -1
    assert rlp.compare_length(data, 0) == 0
    assert rlp.compare_length(data, -1) == 1

def test_favor_short_string_form():
    data = rlp.utils.decode_hex('b8056d6f6f7365')
    with pytest.raises(rlp.exceptions.DecodingError):
        rlp.decode(data)

    data = rlp.utils.decode_hex('856d6f6f7365')
    assert rlp.decode(data) == b'moose'
