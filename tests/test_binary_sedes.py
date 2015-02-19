import pytest
from rlp import SerializationError
from rlp.sedes import Binary


def test_binary():
    b1 = Binary()
    for d in ('', 'asdf', '\x00' * 20, bytearray('fdsa')):
        assert b1.serialize(d) == str(d)
    for d in ([], 5, str):
        with pytest.raises(SerializationError):
            b1.serialize(d)

    b2 = Binary.fixed_length(5)
    for d in ('asdfg', '\x00\x01\x02\x03\x04', bytearray('ababa')):
        assert b2.serialize(d) == str(d)
    for d in ('asdf', 'asdfgh', '', 'bababa'):
        with pytest.raises(SerializationError):
            b2.serialize(d)

    b3 = Binary(2, 4)
    for d in ('as', 'dfg', 'hjkl', '\x00\x01\x02'):
        assert b3.serialize(d) == str(d)
    for d in ('', 'a', 'abcde'):
        with pytest.raises(SerializationError):
            b3.serialize(d)

    b4 = Binary(min_length=3)
    for d in ('abc', 'abcd', 'x' * 132):
        assert b4.serialize(d) == str(d)
    for d in ('ab', '', 'a', 'xy'):
        with pytest.raises(SerializationError):
            b4.serialize(d)

    b5 = Binary(max_length=3)
    for d in ('', 'ab', 'abc'):
        assert b5.serialize(d) == str(d)
    for d in ('abcd', 'vwxyz', 'a' * 32):
        with pytest.raises(SerializationError):
            b5.serialize(d)
